const startBtn = document.getElementById('startBtn');
const urlInput = document.getElementById('youtubeUrl');
const statusSection = document.getElementById('statusSection');
const statusText = document.getElementById('statusText');
const stageList = document.getElementById('stageList');
const downloadLink = document.getElementById('downloadLink');

let currentJob = null;
let pollInterval = null;

startBtn.addEventListener('click', async () => {
  const url = urlInput.value.trim();
  if (!url) {
    alert('Please enter a YouTube URL');
    return;
  }
  startBtn.disabled = true;
  statusSection.classList.remove('hidden');
  statusText.textContent = 'Submitting job...';
  stageList.innerHTML = '';
  downloadLink.classList.add('hidden');

  try {
    const response = await fetch('/api/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await response.json();
    currentJob = data.job_id;
    renderStages(data.stages);
    statusText.textContent = `Job ${currentJob} created. Running pipeline...`;
    pollInterval = setInterval(fetchStatus, 2000);
  } catch (err) {
    statusText.textContent = 'Failed to create job';
  } finally {
    startBtn.disabled = false;
  }
});

async function fetchStatus() {
  if (!currentJob) return;
  const response = await fetch(`/api/jobs/${currentJob}`);
  const data = await response.json();
  renderStages(data.stages);
  statusText.textContent = `Status: ${data.status}`;
  if (data.status === 'completed') {
    clearInterval(pollInterval);
    downloadLink.href = `/api/jobs/${currentJob}/download`;
    downloadLink.classList.remove('hidden');
    statusText.textContent = 'Karaoke video is ready!';
  }
  if (data.error) {
    clearInterval(pollInterval);
    statusText.textContent = `Failed: ${data.error}`;
  }
}

function renderStages(stages) {
  stageList.innerHTML = '';
  Object.entries(stages).forEach(([name, stage]) => {
    const li = document.createElement('li');
    li.className = 'stage-item';
    const label = document.createElement('span');
    label.textContent = name;
    const badge = document.createElement('span');
    badge.className = `badge ${stage.status}`;
    badge.textContent = stage.status;
    li.appendChild(label);
    li.appendChild(badge);
    stageList.appendChild(li);
  });
}
