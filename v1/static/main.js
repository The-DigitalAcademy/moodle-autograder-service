const form = document.getElementById("jobForm");
const jobsDiv = document.getElementById("jobs");
let jobs = [];

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const jobData = {
        userid: document.getElementById("userid").value,
        assignmentid: document.getElementById("assignmentid").value,
        github_link: document.getElementById("github_link").value,
        assignmentname: document.getElementById("assignmentname").value,
        assignmentactivity: document.getElementById("assignmentactivity").value,
        assignmentintro: document.getElementById("assignmentintro").value,
        rubric_key: document.getElementById("rubric_key").value
    };

    const res = await fetch("/grade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(jobData)
    });

    const data = await res.json();
    if(data.job_id){
        jobs.push({job_id: data.job_id, status: "queued"});
        renderJobs();
    }
});

setInterval(async () => {
    for(let job of jobs){
        const res = await fetch(`/grade_status/${job.job_id}`);
        const data = await res.json();
        job.status = data.status;
        job.result = data.result;
    }
    renderJobs();
}, 3000);

function renderJobs(){
    jobsDiv.innerHTML = "";
    jobs.forEach(job => {
        const div = document.createElement("div");
        div.className = "job";
        div.innerHTML = `
            <p>Job ID: ${job.job_id}</p>
            <p class="status">Status: ${job.status}</p>
            <pre>${job.result ? JSON.stringify(job.result, null, 2) : ""}</pre>
        `;
        jobsDiv.appendChild(div);
    });
}
