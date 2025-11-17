document.getElementById('scrapeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const keyword = document.getElementById('keyword').value.trim();
    const hashtag = document.getElementById('hashtag').value.trim();
    const username = document.getElementById('username').value.trim();
    const tweet_url = document.getElementById('tweet_url').value.trim();
    const num_tweets = document.getElementById('num_tweets').value;
    
    // Validate at least one field is filled
    if (!keyword && !hashtag && !username && !tweet_url) {
        showResult('Please fill in at least one search field', true);
        return;
    }
    
    // Show loading state
    const scrapeBtn = document.getElementById('scrapeBtn');
    const statusDiv = document.getElementById('status');
    const resultDiv = document.getElementById('result');
    
    scrapeBtn.disabled = true;
    scrapeBtn.textContent = 'Scraping...';
    statusDiv.classList.remove('hidden');
    resultDiv.classList.add('hidden');
    
    try {
        const response = await fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                keyword,
                hashtag,
                username,
                tweet_url,
                num_tweets
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showResult(data.message + '<br><strong>Job ID:</strong> ' + data.job_id, false);
            
            // Poll for status updates
            pollStatus(data.job_id);
        } else {
            showResult(data.error || 'An error occurred', true);
            resetButton();
        }
        
    } catch (error) {
        showResult('Network error: ' + error.message, true);
        resetButton();
    }
});

async function pollStatus(jobId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${jobId}`);
            const data = await response.json();
            
            if (data.status === 'completed') {
                clearInterval(interval);
                showResult(`✅ Scraping completed!<br><strong>File saved:</strong> ${data.filename}`, false);
                resetButton();
            } else if (data.status === 'failed') {
                clearInterval(interval);
                showResult(`❌ Scraping failed: ${data.error}`, true);
                resetButton();
            } else {
                document.getElementById('statusText').textContent = 'Scraping in progress... Please wait.';
            }
        } catch (error) {
            clearInterval(interval);
            showResult('Error checking status: ' + error.message, true);
            resetButton();
        }
    }, 3000); // Check every 3 seconds
}

function showResult(message, isError) {
    const resultDiv = document.getElementById('result');
    const statusDiv = document.getElementById('status');
    
    statusDiv.classList.add('hidden');
    resultDiv.innerHTML = message;
    resultDiv.classList.remove('hidden');
    
    if (isError) {
        resultDiv.classList.add('error');
    } else {
        resultDiv.classList.remove('error');
    }
}

function resetButton() {
    const scrapeBtn = document.getElementById('scrapeBtn');
    scrapeBtn.disabled = false;
    scrapeBtn.textContent = 'Start Scraping';
}
