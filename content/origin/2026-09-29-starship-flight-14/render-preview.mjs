import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const dir=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(dir,'../../..');
execFileSync(process.execPath,[path.join(root,'.agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs'),path.join(dir,'index.md'),'--style','warm-editorial'],{stdio:'inherit'});
const channel=path.join(root,'content/wechat',path.basename(dir));
fs.mkdirSync(channel,{recursive:true});
const assetPrefix=path.relative(channel,path.join(dir,'assets')).split(path.sep).join('/');
// Article-specific timeline table: reserve most of the width for explanations.
// Put horizontal padding inside each cell: WeChat may strip box-sizing.
const widths=[22,24,54];
const previewPath=path.join(dir,'index.wechat-preview.html');
const tuned=fs.readFileSync(previewPath,'utf8').replace(/<section style="[^"]*border-top:1\.5px[^"]*">[\s\S]*?<\/section>/g,table=>{
  if(!table.includes('进展与边界')) return table;
  let cellIndex=0;
  return table.replace(/<div style="([^"]*flex:0 0 (?:30|35)%;[^"]*)">([\s\S]*?)<\/div>/g,(_,style,content)=>{
    const column=cellIndex++%3;
    const kept=style.split(';').filter(d=>!['width','flex','padding','box-sizing'].includes(d.split(':')[0].trim())).join(';');
    if(column===0 && /^\d{4}\.\d{2}\.\d{2}$/.test(content)) content=`<span style="display:inline-block;">${content.slice(0,5)}</span><span style="display:inline-block;">${content.slice(5)}</span>`;
    return `<div style="${kept};width:${widths[column]}%;flex:0 0 ${widths[column]}%;min-width:0;padding:10px 0;"><div style="padding:0 6px;overflow-wrap:anywhere;">${content}</div></div>`;
  });
});
fs.writeFileSync(previewPath,tuned);
const html=tuned.replaceAll('src="assets/',`src="${assetPrefix}/`);
fs.writeFileSync(path.join(channel,'index.html'),html);
console.log(path.join(channel,'index.html'));
