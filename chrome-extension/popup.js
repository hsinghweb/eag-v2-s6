document.addEventListener('DOMContentLoaded', function() {
  const queryInput = document.getElementById('query-input');
  const submitBtn = document.getElementById('submit-btn');
  const resultDiv = document.getElementById('result');
  const loader = document.getElementById('loader');

  // Add some basic styles
  const style = document.createElement('style');
  style.textContent = `
    .result-container {
      margin: 4px 0 0 0;
      padding: 0;
      font-family: 'Segoe UI', Roboto, Arial, sans-serif;
      font-size: 13px;
      line-height: 1.4;
      width: 100%;
    }
    .query-display {
      display: flex;
      align-items: flex-start;
      margin: 0 0 4px 0;
      padding: 4px 6px;
      background: #f0f7ff;
      border-radius: 2px;
      border-left: 2px solid #4285f4;
      color: #202124;
      font-weight: 500;
      width: 100%;
      box-sizing: border-box;
      gap: 6px;
    }
    .result-item {
      display: flex;
      align-items: flex-start;
      margin: 0;
      padding: 0;
      background: transparent;
      width: 100%;
      gap: 6px;
    }
    .result-item.error {
      background: #ffebee;
      border-left: 2px solid #f44336;
    }
    .label {
      flex: 0 0 auto;
      font-weight: 600;
      color: #1a73e8;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      padding: 2px 0;
    }
    .result-value {
      flex: 1;
      padding: 2px 0 2px 6px;
      margin: 0;
      color: #202124;
      font-family: 'Roboto Mono', 'Courier New', monospace;
      font-size: 13px;
      white-space: pre-wrap;
      word-break: break-word;
      border-left: 2px solid #34a853;
      padding-left: 6px;
    }
    .result-value-inline {
      flex: 1;
      padding: 2px 0;
      color: inherit;
      font-family: inherit;
    }
    #loader {
      display: none;
      margin: 10px 0;
      color: #666;
    }
    #query-input {
      width: 100%;
      padding: 8px;
      margin-bottom: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    #submit-btn {
      background-color: #4285f4;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
    }
    #submit-btn:disabled {
      background-color: #cccccc;
      cursor: not-allowed;
    }
  `;
  document.head.appendChild(style);

  // Handle Enter key in the input field
  queryInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      sendQuery();
    }
  });

  // Handle button click
  submitBtn.addEventListener('click', sendQuery);

  function tryParseJson(responseText) {
    try {
      let resultData = JSON.parse(responseText);
      if (typeof resultData === 'string') {
        try {
          const innerJson = JSON.parse(resultData);
          if (typeof innerJson === 'object' && innerJson !== null) {
            resultData = innerJson;
          }
        } catch (e) {
          console.warn('Inner JSON parse failed, using as-is:', e);
        }
      }
      return { data: resultData, error: null };
    } catch (e) {
      return { data: null, error: e };
    }
  }

  function formatResultHTML(query, resultData, responseText) {
    if (!resultData) {
      return `
        <div class="result-container">
          <div class="query-display">Query: ${query}</div>
          <div class="result-item">
            <div class="result-label">Result</div>
            <div class="result-value">${responseText}</div>
          </div>
        </div>
      `;
    }

    if (resultData.query && resultData.result) {
      return `
        <div class="result-container">
          <div class="query-display">
            <span class="label">Query:</span>
            <span class="result-value-inline">${resultData.query}</span>
          </div>
          <div class="result-item">
            <span class="label">Result:</span>
            <span class="result-value">${resultData.result}</span>
          </div>
        </div>
      `;
    } else if (resultData.result) {
      let cleanResult = resultData.result;
      if (cleanResult.includes('Query:') && cleanResult.includes('Result:')) {
        cleanResult = cleanResult.split('Result:')[1]?.trim() || cleanResult;
      }
      return `
        <div class="result-container">
          <div class="result-item">
            <span class="label">Result:</span>
            <span class="result-value">${cleanResult}</span>
          </div>
        </div>
      `;
    } else {
      return `
        <div class="result-container">
          <div class="result-item">
            <pre>${JSON.stringify(resultData, null, 2)}</pre>
          </div>
        </div>
      `;
    }
  }

  async function sendQuery() {
    const query = queryInput.value.trim();

    if (!query) {
      resultDiv.textContent = 'Please enter a query';
      return;
    }

    loader.style.display = 'block';
    resultDiv.textContent = '';
    submitBtn.disabled = true;

    try {
      const response = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query })
      });

      let responseText = await response.text();
      const { data: resultData, error: parseError } = tryParseJson(responseText);

      if (parseError) {
        console.error('Error parsing JSON:', parseError);
        resultDiv.innerHTML = formatResultHTML(query, null, responseText);
        return;
      }

      try {
        resultDiv.innerHTML = formatResultHTML(query, resultData, responseText);
      } catch (e) {
        console.error('Error formatting response:', e);
        resultDiv.textContent = 'Error: Could not format the response';
      }

    } catch (error) {
      console.error('Error:', error);
      resultDiv.textContent = 'Failed to connect to the Math Agent server. Make sure the server is running.';
    } finally {
      loader.style.display = 'none';
      submitBtn.disabled = false;
    }
  }
});
