const form = document.getElementById('jobForm');
const jobsDiv = document.getElementById('jobs');
let jobs = [];

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        userid: document.getElementById('userid').value,
        assignmentid: document.getElementById('assignmentid').value,
        github_link: document.getElementById('github_link').value,
        assignmentname: document.getElementById('assignmentname').value,
        assignmentactivity: document.getElementById('assignmentactivity').value,
        assignmentrubric: (() => {
            try { return JSON.parse(document.getElementById('rubric').value || '{}'); } catch(e) { return {}; }
        })()
    };
    const res = await fetch('/grade', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    if(data.job_id) {
        jobs.unshift({job_id: data.job_id, status: 'queued'});
        render();
    } else if (data.error) {
        alert('Error: ' + data.error);
    }
});

async function refreshStatuses() {
    for (let j of jobs.slice(0,10)) {
        const res = await fetch(`/grade_status/${j.job_id}`);
        if (res.ok) {
            const d = await res.json();
            j.status = d.status;
            j.result = d.result;
        }
    }
    render();
}

function render() {
    jobsDiv.innerHTML = '';
    for (let j of jobs) {
        const div = document.createElement('div');
        div.style.background = '#fff';
        div.style.padding = '10px';
        div.style.marginBottom = '8px';
        div.innerHTML = `<strong>Job ${j.job_id}</strong><div>Status: ${j.status}</div><pre>${j.result ? JSON.stringify(j.result, null, 2) : ''}</pre>`;
        jobsDiv.appendChild(div);
    }
}

setInterval(refreshStatuses, 3000);
