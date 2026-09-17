import assert from 'node:assert/strict';
import {buildPrompt,draw,wrap,initial,brandDefault,formats} from '../lib/studio.ts';
function context(){return {font:'20px Arial',fillStyle:'',rects:[],text:[],fillRect(){},drawImage(){},createLinearGradient(){return {addColorStop(){}}},measureText(t){return {width:t.length*parseFloat(this.font)*.52}},save(){},restore(){},beginPath(){},rect(...v){this.rects.push(v)},clip(){},fillText(...v){this.text.push(v)},strokeRect(){},setLineDash(){}}}
for(const format of Object.keys(formats)){const f=formats[format],ctx=context(),canvas={getContext:()=>ctx};const c={...initial,format,top:f.top,bottom:f.bottom,right:f.right};const r=draw(canvas,c,brandDefault,null);assert.equal(r.overflow,false,format+' default copy fits');assert.equal(canvas.width,f.w);assert.equal(canvas.height,f.h);const [x,y,w,h]=ctx.rects[0];assert.equal(y,f.h*f.top/100);assert.ok(Math.abs(y+h-f.h*(1-f.bottom/100))<.001);for(const [text,tx,ty]of ctx.text){assert.ok(tx>=x&&tx<=x+w);assert.ok(ty>=y&&ty<y+h,format+' text within safe area');}}
const ctx=context();assert.ok(wrap(ctx,'supercalifragilisticexpialidocious',70).every(line=>ctx.measureText(line).width<=70));
const canvas={getContext:()=>context()};assert.equal(draw(canvas,{...initial,headline:'Very long message '.repeat(300)},brandDefault,null).overflow,true);
const p=buildPrompt({...initial,top:20,bottom:30,right:19,custom:'Blue linen'},brandDefault,'Source facts');for(const s of ['top 20%','bottom 30%','right 19%','Blue linen','Source facts','BACKGROUND ONLY'])assert.ok(p.includes(s));
console.log('Layout checks passed: five export sizes, safe bounds, long words, overflow and prompt composition.');
const {cropGeometry}=await import('../lib/studio.ts');
for(const [iw,ih] of [[1080,1920],[1600,900],[900,1600],[1000,1000]]){
 for(const {w,h}of Object.values(formats)){
  const left=cropGeometry(w,h,iw,ih,{cropZoom:115,cropX:0,cropY:0});
  const right=cropGeometry(w,h,iw,ih,{cropZoom:115,cropX:100,cropY:100});
  assert.ok(right.x<left.x&&right.y<left.y,'Both crop axes move after zoom');
  for(const pos of [0,25,50,75,100]){
   const g=cropGeometry(w,h,iw,ih,{cropZoom:115,cropX:pos,cropY:pos});
   assert.ok(g.x<=0&&g.y<=0&&g.x+g.width>=w-.001&&g.y+g.height>=h-.001,'Crop always covers output');
  }
 }
}
const neutral=cropGeometry(1080,1920,1080,1920,{cropX:50,cropY:50});
assert.equal(neutral.width,1080);assert.equal(neutral.height,1920);
console.log('Crop checks passed: horizontal/vertical movement, no exposed edges, and existing compositions preserved.');
