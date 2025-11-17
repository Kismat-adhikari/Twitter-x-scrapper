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
    // Show tweets container
    document.getElementById('tweetsContainer').style.display = 'block';
    
    const interval = setInterval(async () => {
        try {
            // Get status
            const statusResponse = await fetch(`/status/${jobId}`);
            const statusData = await statusResponse.json();
            
            // Update progress bar
            if (statusData.progress !== undefined) {
                const progressBar = document.getElementById('progressBar');
                const progressText = document.getElementById('progressText');
                const progressInfo = document.getElementById('progressInfo');
                
                progressBar.style.width = statusData.progress + '%';
                progressText.textContent = statusData.progress + '%';
                progressInfo.textContent = `${statusData.current || 0} / ${statusData.target || 0} tweets`;
            }
            
            // Get tweets
            const tweetsResponse = await fetch(`/tweets/${jobId}`);
            const tweetsData = await tweetsResponse.json();
            
            if (tweetsData.tweets) {
                updateTweetsTable(tweetsData.tweets);
            }
            
            // Check if completed
            if (statusData.status === 'completed') {
                clearInterval(interval);
                showResult(`✅ Scraping completed!<br><strong>File saved:</strong> ${statusData.filename}<br><strong>Total tweets:</strong> ${tweetsData.count}`, false);
                resetButton();
            } else if (statusData.status === 'failed') {
                clearInterval(interval);
                showResult(`❌ Scraping failed: ${statusData.error}`, true);
                resetButton();
            }
        } catch (error) {
            clearInterval(interval);
            showResult('Error checking status: ' + error.message, true);
            resetButton();
        }
    }, 2000); // Check every 2 seconds
}

function updateTweetsTable(tweets) {
    const tbody = document.getElementById('tweetsBody');
    tbody.innerHTML = ''; // Clear existing rows
    
    tweets.forEach(tweet => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${tweet.tweet_id || ''}</td>
            <td>@${tweet.username || ''}</td>
            <td>${tweet.display_name || ''}</td>
            <td class="tweet-text" title="${tweet.text || ''}">${tweet.text || ''}</td>
            <td>${formatTimestamp(tweet.timestamp)}</td>
            <td>${tweet.likes || '0'}</td>
            <td>${tweet.retweets || '0'}</td>
            <td>${tweet.replies || '0'}</td>
            <td>${tweet.hashtags || ''}</td>
            <td>${tweet.mentions || ''}</td>
            <td>${tweet.tweet_type || 'original'}</td>
            <td><a href="${tweet.tweet_url || '#'}" target="_blank" class="tweet-link">View</a></td>
        `;
        tbody.appendChild(row);
    });
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString();
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
