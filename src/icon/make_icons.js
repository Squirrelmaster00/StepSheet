/* Builds every StepSheet icon from one drawing, so the page, the installed app,
   the extension and the browser tab all show the same mark.
   Run from the repo root:  node src/icon/make_icons.js   (needs Playwright) */
const { chromium } = require('playwright'); const fs=require('fs'); const path=require('path');
const ROOT=path.resolve(__dirname,'..','..');
const NAVY='#232d3b', Y='#FFFF00', B='#5b8cff', R='#FF3B30', O='#FF6347';
// The four step shapes in a 100x100 box: Work Content, Verify, Check, Safety.
const shapes=sw=>`<g fill="none" stroke-width="${sw}" stroke-linejoin="round">
  <rect x="24" y="24" width="22" height="22" stroke="${Y}"/>
  <circle cx="65" cy="35" r="11" stroke="${B}"/>
  <polygon points="35,53.5 47.5,76 22.5,76" stroke="${R}"/>
  <polygon points="65,52.5 77.5,65 65,77.5 52.5,65" stroke="${O}"/></g>`;
const tile=(kind,sw)=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">${kind==='round'?`<rect width="100" height="100" rx="22" fill="${NAVY}"/>`:`<rect width="100" height="100" fill="${NAVY}"/>`}${shapes(sw)}</svg>`;
const sw=px=>px<=16?9:px<=32?7.5:px<=48?6.5:5.5;   // thicker lines at small sizes so the shapes stay readable
const out=[ ['icon-512.png',512,'full'],['icon-192.png',192,'full'],['icon-180.png',180,'full'],
  ['extension/icons/icon128.png',128,'round'],['extension/icons/icon48.png',48,'round'],['extension/icons/icon32.png',32,'round'],['extension/icons/icon16.png',16,'round'] ];
(async()=>{ const b=await chromium.launch(); const p=await b.newPage();
  for(const [f,px,kind] of out){ await p.setViewportSize({width:px,height:px});
    await p.setContent(`<html><body style="margin:0;background:transparent">${tile(kind,sw(px)).replace('<svg ','<svg width="'+px+'" height="'+px+'" ')}</body></html>`);
    await p.screenshot({path:path.join(ROOT,f),omitBackground:true,clip:{x:0,y:0,width:px,height:px}}); console.log('wrote',f); }
  fs.writeFileSync(path.join(__dirname,'favicon.svg'),tile('round',5.5));
  fs.writeFileSync(path.join(__dirname,'mark.svg'),`<svg xmlns="http://www.w3.org/2000/svg" viewBox="20 20 60 60">${shapes(6.5)}</svg>`);
  console.log('wrote src/icon/favicon.svg, src/icon/mark.svg'); await b.close(); })();
