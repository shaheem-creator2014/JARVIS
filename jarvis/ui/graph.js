/* Canvas force layout: spatial buckets, cutoff repulsion, collision-aware labels. */
const TYPE_COLORS = {md:'#f0c647',txt:'#e5edf5',html:'#36d2ef',css:'#ac80ef',js:'#498cf7',py:'#4cdda2',ino:'#ff9d51',pdf:'#f774bc',json:'#91abbc'};
class KnowledgeGraph {
  constructor(canvas, select) {
    this.canvas=canvas; this.ctx=canvas.getContext('2d'); this.select=select;
    this.nodes=[]; this.edges=[]; this.hidden=new Set(); this.scale=1; this.pan={x:0,y:0}; this.labels=true; this.active=null; this.path=new Set(); this.hover=null; this.drag=null; this.frame=0;
    new ResizeObserver(()=>this.resize()).observe(canvas);
    canvas.addEventListener('pointerdown',e=>this.down(e));
    canvas.addEventListener('pointermove',e=>this.move(e));
    canvas.addEventListener('pointerup',e=>this.up(e));
    canvas.addEventListener('pointercancel',()=>{this.drag=null;});
    canvas.addEventListener('pointerleave',()=>{this.hover=null;});
    canvas.addEventListener('wheel',e=>{e.preventDefault(); const p=this.position(e),old=this.scale;this.scale=Math.max(.2,Math.min(4,this.scale*Math.exp(-e.deltaY*.001)));this.pan.x=p.x-(p.x-this.pan.x)*this.scale/old;this.pan.y=p.y-(p.y-this.pan.y)*this.scale/old;},{passive:false});
    requestAnimationFrame(()=>this.tick());
  }
  resize(){this.w=this.canvas.clientWidth;this.h=this.canvas.clientHeight;const d=Math.min(devicePixelRatio||1,2);this.canvas.width=this.w*d;this.canvas.height=this.h*d;this.ctx.setTransform(d,0,0,d,0,0);if(!this.pan.x)this.fit();}
  set(data){this.nodes=data.nodes.map((n,i)=>({...n,x:Math.cos(i*2.399)*Math.sqrt(i+1)*32,y:Math.sin(i*2.399)*Math.sqrt(i+1)*32,vx:0,vy:0,r:4+Math.min(11,Math.sqrt(n.connections)*1.8)}));this.map=new Map(this.nodes.map(n=>[n.id,n]));this.edges=data.edges.map(e=>({...e,a:this.map.get(e.source),b:this.map.get(e.target)})).filter(e=>e.a&&e.b);this.adj=new Map(this.nodes.map(n=>[n.id,[]]));this.edges.forEach(e=>{this.adj.get(e.source).push(e.target);this.adj.get(e.target).push(e.source);});this.frame=0;this.active=null;this.path.clear();for(let i=0;i<120;i++)this.physics();this.fit();}
  fit(){const w=this.w||600,h=this.h||500;if(!this.nodes.length){this.pan={x:w/2,y:h/2};this.scale=1;return;}const xs=this.nodes.map(n=>n.x),ys=this.nodes.map(n=>n.y);const left=Math.min(...xs)-40,right=Math.max(...xs)+90,top=Math.min(...ys)-45,bottom=Math.max(...ys)+45;this.scale=Math.max(.15,Math.min(2,(w-80)/(right-left),(h-120)/(bottom-top)));this.pan={x:w/2-(left+right)/2*this.scale,y:h/2-(top+bottom)/2*this.scale};}
  position(e){const b=this.canvas.getBoundingClientRect();return{x:e.clientX-b.left,y:e.clientY-b.top};}
  world(p){return{x:(p.x-this.pan.x)/this.scale,y:(p.y-this.pan.y)/this.scale};}
  hit(p){return this.nodes.find(n=>!this.hidden.has(n.type)&&Math.hypot(p.x-n.x,p.y-n.y)<n.r+6/this.scale);}
  down(e){const p=this.position(e),n=this.hit(this.world(p));this.drag={node:n,start:p,last:p,moved:false,shift:e.shiftKey};this.canvas.setPointerCapture(e.pointerId);}
  move(e){const p=this.position(e);if(this.drag){const d=this.drag;d.moved=d.moved||Math.hypot(p.x-d.start.x,p.y-d.start.y)>4;if(d.node){d.node.x+=(p.x-d.last.x)/this.scale;d.node.y+=(p.y-d.last.y)/this.scale;d.node.vx=d.node.vy=0;}else{this.pan.x+=p.x-d.last.x;this.pan.y+=p.y-d.last.y;}d.last=p;}else{this.hover=this.hit(this.world(p));this.canvas.style.cursor=this.hover?'pointer':'grab';}}
  up(){if(this.drag&&!this.drag.moved&&this.drag.node){const n=this.drag.node;if(this.drag.shift&&this.active){this.shortest(this.active.id,n.id);}else{this.active=n;this.path.clear();}this.select(n);}this.drag=null;}
  focus(id){const n=this.map?.get(id);if(n){this.active=n;this.path.clear();this.select(n);}}
  shortest(start,end){const queue=[start],prev=new Map([[start,null]]);for(let i=0;i<queue.length;i++){const v=queue[i];if(v===end)break;for(const next of this.adj.get(v)||[]){if(!prev.has(next)&&!this.hidden.has(this.map.get(next).type)){prev.set(next,v);queue.push(next);}}}this.path.clear();if(prev.has(end)){for(let v=end;v!==null;v=prev.get(v))this.path.add(v);}}
  physics(){const cell=100,grid=new Map();for(const n of this.nodes){const k=`${Math.floor(n.x/cell)},${Math.floor(n.y/cell)}`;if(!grid.has(k))grid.set(k,[]);grid.get(k).push(n);n.vx-=n.x*.0002;n.vy-=n.y*.0002;}
    for(const n of this.nodes){const cx=Math.floor(n.x/cell),cy=Math.floor(n.y/cell);for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)for(const b of grid.get(`${cx+dx},${cy+dy}`)||[]){if(n===b)continue;let x=n.x-b.x,y=n.y-b.y,d=x*x+y*y;if(d>10000)continue;if(d<1){x=.1;y=.1;d=1;}const distance=Math.sqrt(d),minimum=n.r+b.r+12;const f=Math.min(1.8,600/d)*.055+(distance<minimum?(minimum-distance)*.07/distance:0);n.vx+=x*f;n.vy+=y*f;}}
    for(const e of this.edges){const x=e.b.x-e.a.x,y=e.b.y-e.a.y,d=Math.hypot(x,y)||1,f=(d-110-e.a.r-e.b.r)*.003/Math.sqrt(Math.max(e.a.connections,e.b.connections,1));e.a.vx+=x/d*f;e.a.vy+=y/d*f;e.b.vx-=x/d*f;e.b.vy-=y/d*f;}
    for(const n of this.nodes){if(this.drag?.node!==n){n.vx*=.86;n.vy*=.86;n.x+=n.vx;n.y+=n.vy;}}
  }
  tick(){this.frame++;if(this.frame<700||this.drag)this.physics();this.draw();requestAnimationFrame(()=>this.tick());}
  draw(){const c=this.ctx;if(!c)return;c.clearRect(0,0,this.w,this.h);c.save();c.translate(this.pan.x,this.pan.y);c.scale(this.scale,this.scale);
    const focus=this.hover,connected=new Set(focus?[focus.id,...(this.adj?.get(focus.id)||[])]:[]);const idle=!matchMedia('(prefers-reduced-motion: reduce)').matches&&this.edges.length&&Math.floor(this.frame/90)%5===0?this.edges[Math.floor(this.frame/450)%this.edges.length]:null;
    for(const e of this.edges){if(this.hidden.has(e.a.type)||this.hidden.has(e.b.type))continue;const highlighted=this.path.has(e.source)&&this.path.has(e.target)||focus&&(e.a===focus||e.b===focus);c.globalAlpha=focus&&!highlighted ? .1 : 1;c.strokeStyle=highlighted?'#7ce8fb':e===idle?'#36bfdc88':'#31505e4a';c.lineWidth=(highlighted?1.5:.6)/this.scale;c.beginPath();c.moveTo(e.a.x,e.a.y);c.lineTo(e.b.x,e.b.y);c.stroke();}
    for(const n of this.nodes){if(this.hidden.has(n.type))continue;c.globalAlpha=focus&&!connected.has(n.id) ? .1 : 1;const color=TYPE_COLORS[n.type]||'#91abbc';c.fillStyle=color;c.shadowColor=color;c.shadowBlur=n===this.active?22:10;c.beginPath();c.arc(n.x,n.y,n.r,0,Math.PI*2);c.fill();c.shadowBlur=0;if(n===this.active){c.strokeStyle='#e3f6ff';c.lineWidth=1/this.scale;c.beginPath();c.arc(n.x,n.y,n.r+5,0,Math.PI*2);c.stroke();}}
    c.globalAlpha=1;if(this.labels){c.font=`${10/Math.max(.8,this.scale)}px monospace`;const boxes=[];for(const n of [...this.nodes].sort((a,b)=>b.connections-a.connections)){if(this.hidden.has(n.type)||focus&&!connected.has(n.id))continue;const label=n.name.slice(0,25),width=c.measureText(label).width,x=n.x+n.r+5,y=n.y;const box={x,y:y-10,w:width,h:13};if(boxes.some(b=>box.x<b.x+b.w&&box.x+box.w>b.x&&box.y<b.y+b.h&&box.y+box.h>b.y))continue;if(boxes.length>=45)break;boxes.push(box);c.fillStyle=n===this.active?'#eafaff':'#bccbd4';c.fillText(label,x,y+3);}}
    c.restore();if(!this.nodes.length){c.fillStyle='#536675';c.font='13px system-ui';c.textAlign='center';c.fillText('Request indexing to map your workspace.',this.w/2,this.h/2);c.textAlign='left';}}
}
