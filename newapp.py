from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://samiksha:password123@localhost:5432/ecommerce_data"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the SalesData model for your sales_data table
class SalesData(db.Model):
    __tablename__ = 'sales_data'

    InvoiceNo = db.Column(db.String(20), primary_key=True)
    StockCode = db.Column(db.String(20))
    Description = db.Column(db.Text)
    Quantity = db.Column(db.Integer) 
    InvoiceDate = db.Column(db.DateTime)
    UnitPrice = db.Column(db.Numeric(10, 2))
    CustomerID = db.Column(db.String(20))
    Country = db.Column(db.String(50))

# Define the RecommendationEngine class
class RecommendationEngine:
    def __init__(self):
        self.user_item_matrix = None
        self.similarity_matrix = None
        self.products = None
    
    def train(self):
        # Fetch all sales data
        sales_df = pd.read_sql(
            db.session.query(SalesData).statement,
            db.engine
        )

        if sales_df.empty:
            raise ValueError("No sales data available to train the model.")
        
        # Create user-item matrix (customers x products)
        user_item = sales_df.pivot_table(
            index='CustomerID',
            columns='StockCode',
            values='Quantity',
            aggfunc='sum',
            fill_value=0
        )

        if user_item.empty:
            raise ValueError("User-item matrix is empty after pivoting.")

        # Calculate similarity matrix using cosine similarity
        self.similarity_matrix = cosine_similarity(user_item)
        print("Similarity Matrix:", self.similarity_matrix)  # Debug print

        self.user_item_matrix = user_item

        # Store product information
        self.products = sales_df[['StockCode', 'Description']].drop_duplicates()

    def get_recommendations(self, customer_id, n_recommendations=5):
        if self.user_item_matrix is None or self.similarity_matrix is None:
            raise ValueError("Recommendation model is not trained yet.")
        
        if customer_id not in self.user_item_matrix.index:
            return self._get_popular_products(n_recommendations)
        
        user_idx = self.user_item_matrix.index.get_loc(customer_id)
        similar_users = self.similarity_matrix[user_idx].argsort()[::-1][1:6]
        
        # Get products bought by similar users
        recommendations = defaultdict(float)
        for similar_user_idx in similar_users:
            similar_user_id = self.user_item_matrix.index[similar_user_idx]
            similarity_score = self.similarity_matrix[user_idx][similar_user_idx]  # Ensure similarity_score is scalar
            
            # Get products bought by similar user
            user_purchases = self.user_item_matrix.loc[similar_user_id]
            
            user_purchases = user_purchases.to_dict()  # Convert to dictionary

            for product, quantity in user_purchases.items():
                if quantity > 0:  # Ensure we're only considering products purchased
                    recommendations[product] += similarity_score * quantity

        # Sort and get top recommendations
        top_products = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:n_recommendations]
        
        # Get product details
        recommended_products = []
        for stock_code, score in top_products:
            if self.products is None or self.products.empty:
                raise ValueError("Product data is not available.")
            
            product_info = self.products[self.products['StockCode'] == stock_code]
            if not product_info.empty:
                product_info = product_info.iloc[0].to_dict()  # Convert row to dict

                recommended_products.append({
                    'stock_code': stock_code,
                    'description': product_info.get('Description', ''),
                    'score': float(score)
                })

        return recommended_products

    def _get_popular_products(self, n_recommendations=5):
        if db.session.bind is None:
            raise ValueError("Database connection not properly initialized.")
        
        purchases_df = pd.read_sql(
            db.session.query(SalesData).statement,
            db.session.bind
        )

        # Calculate the most popular products based on quantity
        popular_products = purchases_df.groupby(['StockCode', 'Description'])['Quantity'].sum() \
            .reset_index() \
            .sort_values('Quantity', ascending=False) \
            .head(n_recommendations)

        recommendations = []
        for _, row in popular_products.iterrows():
            recommendations.append({
                'stock_code': row['StockCode'],
                'description': row['Description'],
                'score': float(row['Quantity'])
            })

        return recommendations


# Initialize recommendation engine
recommendation_engine = RecommendationEngine()

# Test route for verifying the Flask app is running
@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'The Flask app is running!'}), 200

@app.route('/train', methods=['POST'])
def train_model():
    try:
        recommendation_engine.train()
        return jsonify({'message': 'Model trained successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommendations/<string:customer_id>', methods=['GET'])
def get_recommendations(customer_id):
    try:
        n_recommendations = int(request.args.get('n', 5))
        recommendations = recommendation_engine.get_recommendations(
            customer_id, 
            n_recommendations
        )
        return jsonify(recommendations), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

print("Starting the Flask application...")

if __name__ == '__main__':
    print("Running the Flask app...")
    app.run(debug=True, port=5001)
