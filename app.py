from flask import Flask , jsonify , request;
from flask_mysqldb import MySQL;
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS

app=Flask(__name__)
CORS(app)  # Enable CORS for all routes by default


app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_PORT']=3030
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='1234567'
app.config['MYSQL_DB']='skin_walker'
mysql=MySQL(app)


# Configuration for file upload
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Set max size for each file

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route("/view_products", methods=['GET'])
def view_all_products():
    cur = mysql.connection.cursor()

    # Query to retrieve all products
    query = "SELECT * FROM products"
    cur.execute(query)
    
    # Fetch all products
    products = cur.fetchall()
    cur.close()

    # Format the result as a list of dictionaries
    product_list = []
    for product in products:
        product_list.append({
            'id': product[0],
            'name': product[1],
            'price': product[2],
            'description': product[3],
            'benefits': product[4],
            'images': product[5].split(',')  # Splitting images back into a list
        })

    return jsonify({'products': product_list}), 200





@app.route("/add_products", methods=['POST'])
def add_product():
    cur = mysql.connection.cursor()
    
    # Retrieve product details from form data (not JSON)
    product_name = request.form['product_name']
    product_price = request.form['product_price']
    product_description = request.form['product_description']
    product_benefits = request.form['product_benefits']
    
    # Retrieve multiple image files
    product_files = request.files.getlist('product_images')  
    filenames = []

    for file in product_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)

    # Convert the list of filenames to a comma-separated string
    images = ','.join(filenames)

    # Insert product details and image filenames into the database
    query = """
        INSERT INTO products (product_name, product_price, product_description, product_benefits, product_images)
        VALUES (%s, %s, %s, %s, %s)
    """
    cur.execute(query, (product_name, product_price, product_description, product_benefits, images))
    mysql.connection.commit()

    # Close the cursor
    cur.close()

    return jsonify({'message': 'Product added successfully'}), 201


@app.route("/edit_product/<int:product_id>", methods=['PUT'])
def edit_product(product_id):
    data = request.json
    cur = mysql.connection.cursor()
    query = """
        UPDATE products
        SET product_name = %s, product_price = %s, product_description = %s, product_benefits = %s
        WHERE id = %s
    """
    cur.execute(query, (data['name'], data['price'], data['description'], data['benefits'], product_id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Product updated successfully'}), 200


@app.route("/delete_product/<int:product_id>", methods=['DELETE'])
def delete_product(product_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Product deleted successfully'}), 200



@app.route("/submit_enquiry", methods=['POST'])
def submit_enquiry():
    data = request.json
    name = data.get('name')
    phone_number = data.get('phone_number')
    place = data.get('place')
    pincode = data.get('pincode')
    
    # Validate required fields
    if not all([name, phone_number, place, pincode]):
        return jsonify({'error': 'All fields are required'}), 400

    # Insert data into the database
    try:
        cur = mysql.connection.cursor()
        query = "INSERT INTO enquiries (name, phone_number, place, pincode) VALUES (%s, %s, %s, %s)"
        cur.execute(query, (name, phone_number, place, pincode))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Enquiry submitted successfully'}), 201
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Failed to submit enquiry'}), 500





if __name__ == '__main__':
    app.run(debug=True)