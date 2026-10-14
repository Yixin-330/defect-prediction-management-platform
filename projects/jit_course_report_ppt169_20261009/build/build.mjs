import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from 'file:///C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const root='D:/软件缺陷测试与预测/projects/jit_course_report_ppt169_20261009';
const skill='C:/Users/Lenovo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations';
const runtimePython='C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const workspaceDir='D:/软件缺陷测试与预测';
const finalPath=workspaceDir+'/成果文件/即时软件缺陷预测系统_阶段汇报.pptx';
const p=Presentation.create({slideSize:{width:1280,height:720}});
const tables={
 2:{x:64,y:274,w:1152,widths:[274,878],heights:[48,52,52,52],values:[['核心用户','使用目的'],['学生开发者','查看自己提交的风险并改进代码'],['项目负责人','安排代码审查，了解团队整体风险'],['教师或助教','查看各小组的项目质量趋势，及时提供指导']]},
 3:{x:64,y:174,w:564,widths:[164,400],heights:[56,96,96,96,96],values:[['已完成工作','主要内容'],['产品需求','明确目标用户、使用场景\n与功能需求'],['产品主线','明确提交分析、风险解释、\n审查与处理记录的使用流程'],['小组分工','明确四个角色的主责模块\n与工作内容'],['技术架构','明确系统模块、数据流及\n训练与预测的关系']]},
 6:{x:64,y:158,w:1152,widths:[320,240,592],heights:[52,110,110,110,110],values:[['角色与人员','主责模块','核心工作'],['A．数据与特征工程师\n白沁禾','数据采集、\n特征工程','Git仓库解析、SZZ、Kamei 14维特征、\n数据清洗与持久化、训练集构建'],['B．模型工程师\n张艺馨','模型训练、\n评估与解释','至少8个模型（经典ML与DL）、两类\n评估指标、数据划分、模型对比选型、\nSHAP等解释'],['C．后端与系统工程师\n侯洁','预测服务、\n工程化','在线预测API、数据与模型封装、\n仓库集成或Webhook、CI/CD、\n部署与稳定性'],['D．前端与产品工程师\n张欣悦','可视化、\n产品体验','风险列表、趋势看板、详情页、结果与\n解释展示、交互打磨、产品文档与演示']]},
 7:{x:64,y:170,w:1152,widths:[302,400,450],heights:[52,108,108,108,108],values:[['当前问题','具体表现','应对计划'],['首个可用版本\n边界不够明确','产品主线已明确，首次交付\n功能与验收标准仍需细化','确定首次演示必须跑通的流程，\n划分优先实现与后续扩展功能'],['实验工作量较大','至少8个模型，涉及两类\n指标、模型对比与解释','先跑通基线模型，统一实验\n流程，再逐步扩展模型'],['模块交付约定\n不够具体','数据格式、特征顺序、模型\n文件及接口结构尚需对齐','制定输入输出规范，用公共\n样例数据提前联调'],['训练数据与目标\n用户存在差异','开源项目与高校课程项目的\n规模、提交习惯存在差异','分开开展开源数据评估与课程\n项目试用，验证适用性']]},
 8:{x:64,y:154,w:1152,widths:[312,438,402],heights:[52,96,96,96,96],values:[['阶段','重点工作','阶段交付'],['1．明确交付范围\n与协作规范','确定首次可用功能及验收标准，\n统一数据与接口格式','功能清单、接口约定、\n公共样例数据'],['2．完成数据\n与模型基线','跑通数据采集、标注、特征提取\n和基线评估，逐步扩展模型实验','可复现的数据处理流程、\n模型与评估报告'],['3．完成系统联调','连接仓库接入、预测、风险解释\n与审查记录功能','可运行的完整使用流程'],['4．开展场景验证','邀请课程团队试用，收集反馈\n并检查模型适用性','试用记录、问题清单\n与改进计划']]}
};
const files=(await fs.readdir(root+'/svg_output')).filter(f=>f.endsWith('.svg')).sort();
const noteSource=await fs.readFile(root+'/notes/total.md','utf8');
const notes=Object.fromEntries([...noteSource.matchAll(/## (\w+)\r?\n([\s\S]*?)(?=\r?\n## |$)/g)].map(m=>[m[1],m[2].trim()]));
const attrs=s=>Object.fromEntries([...s.matchAll(/([\w-]+)="([^"]*)"/g)].map(m=>[m[1],m[2]]));
const num=(o,k,d=0)=>Number(o[k]??d);
const decode=s=>s.replaceAll('&amp;','&').replaceAll('&lt;','<').replaceAll('&gt;','>').replaceAll('&quot;','"');
const line=(s,a,b,end=false,start=false)=>s.shapes.add({geometry:'connector',kind:'straight',position:{left:Math.min(a[0],b[0]),top:Math.min(a[1],b[1]),width:Math.abs(b[0]-a[0]),height:Math.abs(b[1]-a[1]),horizontalFlip:b[0]<a[0],verticalFlip:b[1]<a[1]},line:{fill:'#6D8299',width:2},tail:{type:end?'triangle':'none',width:'sm',length:'sm'},head:{type:start?'triangle':'none',width:'sm',length:'sm'}});

for(let i=0;i<files.length;i++){
 const s=p.slides.add();s.background.fill='#FFFFFF';
 const svg=(await fs.readFile(root+'/svg_output/'+files[i],'utf8')).replace(/<defs>[\s\S]*?<\/defs>/g,'').replace(/<g id="native-table">[\s\S]*?<\/g>/g,'');
 for(const m of svg.matchAll(/<(rect|line|polyline|text)\s+([^>]*?)(?:\/>|>([\s\S]*?)<\/text>)/g)){
  const a=attrs(m[2]),tag=m[1];
  if(tag==='rect'){
   if(num(a,'width')===1280&&num(a,'height')===720)continue;
   s.shapes.add({geometry:'rect',name:a.id??'module-or-placeholder',position:{left:num(a,'x'),top:num(a,'y'),width:num(a,'width'),height:num(a,'height')},fill:a.fill??'none',line:{fill:a.stroke??'none',width:num(a,'stroke-width'),style:a['stroke-dasharray']?'dashed':'solid'}});
  } else if(tag==='text'){
   const str=decode(m[3]),sz=num(a,'font-size',24),x=num(a,'x'),y=num(a,'y');
   const estimated=[...str].reduce((v,c)=>v+(c.codePointAt(0)>255?1:0.63),0)*sz+16;
   const sh=s.shapes.add({geometry:'textbox',name:i===0&&sz===52?'cover-title':sz===40?'slide-title':'text-'+s.shapes.items.length,position:{left:x,top:y-sz*1.02,width:Math.min(1280-x-20,estimated),height:sz*1.4},fill:'none',line:{fill:'none',width:0}});
   sh.text=str;sh.text.style={fontSize:sz,typeface:'Microsoft YaHei',bold:a['font-weight']==='700',color:a.fill??'#263444',alignment:'left',verticalAlignment:'top',autoFit:'none',wrap:'none',insets:0};
  } else if(tag==='line'){
   const sh=line(s,[num(a,'x1'),num(a,'y1')],[num(a,'x2'),num(a,'y2')],!!a['marker-end'],!!a['marker-start']);sh.line={fill:a.stroke??'#D4DEE8',width:num(a,'stroke-width',1)};
  } else {
   const points=a.points.trim().split(/\s+/).map(p=>p.split(',').map(Number));
   for(let k=1;k<points.length;k++)line(s,points[k-1],points[k],k===points.length-1&&!!a['marker-end']);
  }
 }
 const cfg=tables[i+1];
 if(cfg){
  const t=s.tables.add({rows:cfg.values.length,columns:cfg.values[0].length,left:cfg.x,top:cfg.y,width:cfg.w,height:cfg.heights.reduce((a,b)=>a+b,0),columnWidths:cfg.widths,values:cfg.values});
  t.styleOptions={headerRow:false,bandedRows:false};
  t.borders.assign({fill:'#D4DEE8',width:1,style:'solid'});
  for(let r=0;r<cfg.values.length;r++){
   t.rows[r].height=cfg.heights[r];
   for(let c=0;c<cfg.values[r].length;c++){
    const cell=t.getCell(r,c);cell.fill=r===0?'#F3F6FA':'#FFFFFF';
    cell.text.style={typeface:'Microsoft YaHei',fontSize:24,bold:r===0||c===0,color:r===0?'#18324F':i===7&&c===2?'#2166AC':'#263444',alignment:'left',verticalAlignment:'middle',autoFit:'none',wrap:'none',lineSpacing:1.1,insets:{left:18,right:18,top:6,bottom:6}};
    t.cells.block({row:r,column:c,rowCount:1,columnCount:1}).assign({margins:{left:18,right:18,top:6,bottom:6},anchor:'center'});
   }
  }
 }
 s.speakerNotes.text=notes[files[i].replace('.svg','')];
 console.log('Built slide '+(i+1));
}
await fs.mkdir(root+'/build/renders',{recursive:true});
await fs.writeFile(root+'/build/deck.json',JSON.stringify(p.toProto()));
const candidatePath=root+'/build/candidate.pptx';
await (await PresentationFile.exportPptx(p)).save(candidatePath);
console.log('Draft exported');
for(let i=0;i<p.slides.items.length;i++){
 const blob=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(root+'/build/renders/slide-'+(i+1)+'.png',new Uint8Array(await blob.arrayBuffer()));
 console.log('Rendered slide '+(i+1));
}
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
const result=await finalizePresentation({workspaceDir,candidatePath,finalPath,pythonExecutable:runtimePython,integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[2,3,6,7,8].flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:8,requiredNativeTableOwnerSlides:[2,3,6,7,8],fontPolicy:{basis:'design',families:['Microsoft YaHei']},verifyArtifactToolImport:true,receiptPath:root+'/build/validation.json'});
console.log(JSON.stringify(result));
