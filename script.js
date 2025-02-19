const apiUrl = 'http://localhost:5001';  // Change this if needed based on your Flask server

function trainModel() {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = 'Training the model...';

    fetch(`${apiUrl}/train`, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            messageDiv.textContent = 'Model trained successfully!';
        } else {
            messageDiv.textContent = `Error: ${data.error}`;
        }
    })
    .catch(error => {
        messageDiv.textContent = `Error: ${error}`;
    });
}

function getRecommendations() {
    const customerId = document.getElementById('customer-id').value;
    const numRecommendations = document.getElementById('num-recommendations').value;
    const recommendationsList = document.getElementById('recommendations-list');
    const messageDiv = document.getElementById('message');
    recommendationsList.innerHTML = '';  // Clear previous recommendations
    messageDiv.textContent = 'Fetching recommendations...';

    if (!customerId) {
        messageDiv.textContent = 'Please enter a customer ID.';
        return;
    }

    fetch(`${apiUrl}/recommendations/${customerId}?n=${numRecommendations}`, {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        recommendationsList.innerHTML = ''; // Clear previous recommendations
        if (Array.isArray(data) && data.length > 0) {
            data.forEach(item => {
                const productCard = document.createElement('div');
                productCard.classList.add('col');

                // Creating the Bootstrap card structure for each product
                productCard.innerHTML = `
                    <div class="card recommendation-card">
                        <img src="images/image.jpg" class="card-img-top" alt="${item.description}">
                        <div class="card-body recommendation-card-body">
                            <h5 class="card-title recommendation-title">${item.description}</h5>
                            <p class="recommendation-score">Stock Code: ${item.stock_code}</p>
                            <p class="recommendation-score">Score: ${item.score.toFixed(2)}</p>
                        </div>
                    </div>
                `;

                // Append the card to the recommendations list
                recommendationsList.appendChild(productCard);
            });
            messageDiv.textContent = 'Recommendations fetched successfully!';
        } else {
            messageDiv.textContent = 'No recommendations found.';
        }
    })
    .catch(error => {
        messageDiv.textContent = `Error: ${error}`;
    });
}