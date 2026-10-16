const $ = (id) => document.getElementById(id);
const state = { page: 1, pageSize: 8, total: 0, pages: 1, searchTimer: null };
const fields = ["student_code","name","date_of_birth","email","phone","course","address","enrollment_date","status"];
const initials = (name="Student") => name.trim().split(/\s+/).slice(0,2).map(p=>p[0]).join("").toUpperCase();
const esc = (value="") => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const prettyDate = (value) => { if(!value) return "—"; const d = new Date(`${value}T00:00:00`); return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"}); };
async function api(url, options={}) {
  const response = await fetch(url, {headers:{"Content-Type":"application/json",...(options.headers||{})}, ...options});
  if(response.status === 204) return null;
  const data = await response.json().catch(()=>({detail:"Unexpected server response"}));
  if(!response.ok) throw new Error(Array.isArray(data.detail) ? data.detail.map(x=>x.msg).join(", ") : (data.detail || "Request failed"));
  return data;
}
function toast(message, error=false){const el=$("toast");el.textContent=message;el.className=`toast show${error?" error":""}`;clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.className="toast",3200);}
function statusClass(status){return status==="Completed"?"status-completed":status==="On Hold"?"status-on-hold":"status-active";}
async function loadStats(){
  const s=await api("/api/stats");
  $("totalStat").textContent=s.total;$("activeStat").textContent=s.active;$("completedStat").textContent=s.completed;$("coursesStat").textContent=s.courses;$("navCount").textContent=s.total;
  $("courseChart").innerHTML=s.course_breakdown.length?s.course_breakdown.map(item=>`<div class="course-row"><span title="${esc(item.course)}">${esc(item.course.length>23?item.course.slice(0,22)+"…":item.course)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(3,Math.round(item.count/Math.max(1,s.total)*100))}%"></div></div><span class="course-count">${item.count}</span></div>`).join(""):'<div class="empty-state">No course data yet.</div>';
  $("recentList").innerHTML=s.recent.length?s.recent.map(item=>`<div class="recent-item"><div class="student-avatar">${esc(initials(item.name))}</div><div class="recent-meta"><strong>${esc(item.name)}</strong><small>${esc(item.course||"Course not specified")} · ${esc(item.student_code||"No ID")}</small></div><span class="recent-date">${esc(prettyDate(item.enrollment_date))}</span></div>`).join(""):'<div class="empty-state">No students added yet.</div>';
  const list=await api("/students?page=1&page_size=100");
  const courses=[...new Set(list.items.map(x=>x.course).filter(Boolean))].sort();
  const select=$("courseFilter"), current=select.value;
  select.innerHTML='<option value="">All courses</option>'+courses.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join("");
  select.value=courses.includes(current)?current:"";
}
async function loadStudents(){
  const params=new URLSearchParams({page:state.page,page_size:state.pageSize});
  const search=$("searchInput").value.trim(),status=$("statusFilter").value,course=$("courseFilter").value;
  if(search)params.set("search",search);if(status)params.set("status",status);if(course)params.set("course",course);
  try{
    const data=await api(`/students?${params.toString()}`);state.total=data.total;state.pages=Math.max(1,data.pages);
    $("studentRows").innerHTML=data.items.length?data.items.map(s=>`<tr>
      <td><div class="student-cell"><div class="student-avatar">${esc(initials(s.name))}</div><div><div class="student-name">${esc(s.name)}</div><div class="student-email">${esc(s.email)}</div></div></div></td>
      <td class="student-code">${esc(s.student_code||`STU-${String(s.id).padStart(4,"0")}`)}</td>
      <td class="course-name">${esc(s.course||"—")}</td><td>${esc(prettyDate(s.enrollment_date))}</td>
      <td><span class="status-badge ${statusClass(s.status)}">${esc(s.status)}</span></td>
      <td><div class="row-actions"><button class="row-action" title="Edit student" aria-label="Edit ${esc(s.name)}" onclick="editStudent(${s.id})">✎</button><button class="row-action" title="Delete student" aria-label="Delete ${esc(s.name)}" onclick="removeStudent(${s.id},'${esc(s.name).replace(/'/g,"&#39;")}')">⌫</button></div></td></tr>`).join(""):'<tr><td colspan="6"><div class="empty-state"><strong>No matching students</strong>Try changing your search or filters.</div></td></tr>';
    $("resultCount").textContent=`Showing ${data.total?((state.page-1)*state.pageSize+1):0}–${Math.min(state.page*state.pageSize,data.total)} of ${data.total} students`;
    $("pageLabel").textContent=`Page ${state.page} of ${state.pages}`;$("prevPage").disabled=state.page<=1;$("nextPage").disabled=state.page>=state.pages;
  }catch(e){$("studentRows").innerHTML=`<tr><td colspan="6" class="empty-state">Could not load records: ${esc(e.message)}</td></tr>`;toast(e.message,true);}
}
async function refresh(){try{await loadStats();await loadStudents();document.querySelector(".status-pill").innerHTML="<i></i> API connected";}catch(e){document.querySelector(".status-pill").textContent="API unavailable";toast("Could not connect to the API. Is the server running?",true);}}
function openModal(student=null){
  $("studentForm").reset();$("formError").textContent="";$("studentDbId").value=student?.id||"";
  $("modalTitle").textContent=student?"Edit student":"Add student";$("saveStudentBtn").textContent=student?"Save changes":"Save student";
  $("enrollment_date").value=student?.enrollment_date||new Date().toISOString().slice(0,10);
  $("status").value=student?.status||"Active";
  if(student) fields.forEach(key=>{if($(key) && student[key]!==null && student[key]!==undefined)$(key).value=student[key];});
  $("studentModal").hidden=false;document.body.style.overflow="hidden";$("name").focus();
}
function closeModal(){$("studentModal").hidden=true;document.body.style.overflow="";}
async function editStudent(id){try{const student=await api(`/students/${id}`);openModal(student);}catch(e){toast(e.message,true);}}
async function removeStudent(id,name){
  if(!confirm(`Delete ${name}'s student record?\nThis action cannot be undone.`))return;
  try{await api(`/students/${id}`,{method:"DELETE"});toast("Student record deleted.");state.page=1;await refresh();}catch(e){toast(e.message,true);}
}
$("studentForm").addEventListener("submit",async event=>{
  event.preventDefault();$("formError").textContent="";
  const payload={};fields.forEach(key=>{const el=$(key);if(el){const value=el.value.trim();payload[key]=value||null;}});
  if(!payload.student_code)delete payload.student_code;
  const id=$("studentDbId").value;
  $("saveStudentBtn").disabled=true;$("saveStudentBtn").textContent="Saving…";
  try{
    await api(id?`/students/${id}`:"/students",{method:id?"PATCH":"POST",body:JSON.stringify(payload)});
    closeModal();toast(id?"Student details updated.":"Student added successfully.");state.page=1;await refresh();
  }catch(e){$("formError").textContent=e.message;}finally{$("saveStudentBtn").disabled=false;$("saveStudentBtn").textContent=id?"Save changes":"Save student";}
});
$("addStudentBtn").addEventListener("click",()=>openModal());
$("closeModal").addEventListener("click",closeModal);$("cancelModal").addEventListener("click",closeModal);
$("studentModal").addEventListener("click",e=>{if(e.target===$("studentModal"))closeModal();});
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!$("studentModal").hidden)closeModal();});
$("searchInput").addEventListener("input",()=>{clearTimeout(state.searchTimer);state.searchTimer=setTimeout(()=>{state.page=1;loadStudents();},250);});
$("statusFilter").addEventListener("change",()=>{state.page=1;loadStudents();});
$("courseFilter").addEventListener("change",()=>{state.page=1;loadStudents();});
$("prevPage").addEventListener("click",()=>{if(state.page>1){state.page--;loadStudents();}});
$("nextPage").addEventListener("click",()=>{if(state.page<state.pages){state.page++;loadStudents();}});
$("refreshBtn").addEventListener("click",refresh);
$("resetFiltersBtn").addEventListener("click",()=>{$("searchInput").value="";$("statusFilter").value="";$("courseFilter").value="";state.page=1;loadStudents();});
$("exportBtn").addEventListener("click",()=>{window.location.href="/students/export/csv";toast("Preparing CSV export…");});
$("dismissNotice").addEventListener("click",()=>{$(".notice").style.display="none";});
refresh();
