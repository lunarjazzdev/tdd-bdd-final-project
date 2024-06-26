# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_read_product(self):
        """Test reading a product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        find_product = Product.find(product.id)
        self.assertEqual(find_product.id, product.id)
        self.assertEqual(find_product.name, product.name)
        self.assertEqual(find_product.description, product.description)
        self.assertEqual(find_product.price, product.price)

    def test_update_product(self):
        """Test updating a product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        id_org = product.id
        description_org = "some-description"
        product.description = description_org
        product.update()
        self.assertEqual(description_org, product.description)
        self.assertEqual(id_org, product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, id_org)
        self.assertEqual(products[0].description, description_org)

    def test_update_product_without_id(self):
        """Test updating a product with empty ID raises DataValidationError"""
        product = ProductFactory()
        product.id = None  # Ensuring the ID is None
        self.assertRaises(DataValidationError, product.update)

    def test_deserialize_product(self):
        """Test deserializing a product"""
        product = Product()
        data = {
            "name": "Test Product",
            "description": "This is a test product",
            "price": "19.99",
            "available": True,
            "category": "FOOD"
        }
        product.deserialize(data)
        self.assertEqual(product.name, data["name"])
        self.assertEqual(product.description, data["description"])
        self.assertEqual(product.price, Decimal(data["price"]))
        self.assertEqual(product.available, data["available"])
        self.assertEqual(product.category, Category.FOOD)

    def test_deserialize_invalid_boolean(self):
        """Test deserializing a product with an invalid boolean raises DataValidationError"""
        product = Product()
        data = {
            "name": "Test Product",
            "description": "This is a test product",
            "price": 19.99,
            "available": "yes",  # Invalid boolean
            "category": "FOOD"
        }
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(data)
        self.assertTrue("Invalid type for boolean [available]" in str(context.exception))

    def test_deserialize_missing_key(self):
        """Test deserializing a product with a missing key raises DataValidationError"""
        product = Product()
        data = {
            "name": "Test Product",
            "description": "This is a test product",
            "available": True,
            "category": "FOOD"
        }
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(data)
        self.assertTrue("Invalid product: missing price" in str(context.exception))

    def test_deserialize_faulty_attribute(self):
        """Test deserializing a product with a faulty attribute raises DataValidationError"""
        product = Product()
        data = {
            "name": "Test Product",
            "description": "This is a test product",
            "price": 19.99,
            "available": True,  # Invalid boolean
            "category": "BLAB"
        }
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(data)
        self.assertTrue("Invalid attribute: " in str(context.exception))

    def test_deserialize_faulty_type(self):
        """Test deserializing a product with a faulty type raises DataValidationError"""
        product = Product()
        data = None
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(data)
        self.assertTrue("Invalid product: body of request contained bad or no data " in str(context.exception))

    def test_delete_product(self):
        """Test deleting a product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        product.delete()
        products = Product.all()
        self.assertEqual(len(products), 0)

    def test_list_all_products(self):
        """Test listing all products"""
        products = Product.all()
        self.assertEqual(len(products), 0)
        for _ in range(5):
            product = ProductFactory()
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_product_by_name(self):
        """Test finding product by name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        find_products = Product.find_by_name(name)
        self.assertEqual(count, find_products.count())
        for product in find_products:
            self.assertEqual(product.name, name)

    def test_find_product_by_availability(self):
        """Test finding products by availability"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        availability = products[0].available
        count = len([product for product in products if product.available == availability])
        available_products = Product.find_by_availability(availability)
        self.assertEqual(count, available_products.count())
        for product in available_products:
            self.assertEqual(product.available, availability)

    def test_find_product_by_category(self):
        """Test finding products by availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        products = Product.find_by_category(category)
        self.assertEqual(count, products.count())
        for product in products:
            self.assertEqual(product.category, category)
