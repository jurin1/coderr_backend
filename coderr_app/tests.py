from django.test import TestCase, Client
from django.urls import reverse
import json

class AuthenticationEndpointTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_registration_post(self):
        url = reverse('registration') # Assuming URL name 'registration'
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
            "repeated_password": "testpassword",
            "type": "customer"
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIn('token', response_json)
        self.assertEqual(response_json['username'], 'testuser')
        self.assertEqual(response_json['email'], 'test@example.com')
        self.assertIn('user_id', response_json)

        # Test 400 Bad Request - missing field
        invalid_data = {
            "email": "test@example.com",
            "password": "testpassword",
            "repeated_password": "testpassword",
            "type": "customer"
        }
        response_invalid = self.client.post(url, json.dumps(invalid_data), content_type='application/json')
        self.assertEqual(response_invalid.status_code, 400)

        # Test 500 Internal Server Error (generic - could be more specific based on your error handling)
        # To test 500, you would need to trigger a server error condition in your view logic.
        # This is harder to simulate generically without knowing your view code.
        # Example (assuming you have a way to force a 500 error):
        # with self.assertRaises(Exception): # Replace Exception with the specific exception your view might raise
        #     self.client.post(url, json.dumps(data), content_type='application/json')


    def test_login_post(self):
        url = reverse('login') # Assuming URL name 'login'
        data = {
            "username": "testuser", # Assuming testuser exists - you might need to create a user in setUp
            "password": "testpassword"
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201) # Doc says 201 for login success
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIn('token', response_json)
        self.assertEqual(response_json['username'], 'testuser')
        self.assertEqual(response_json['email'], 'test@example.com') # Assuming email is returned on login
        self.assertIn('user_id', response_json)

        # Test 400 Bad Request - invalid credentials
        invalid_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response_invalid = self.client.post(url, json.dumps(invalid_data), content_type='application/json')
        self.assertEqual(response_invalid.status_code, 400) # Or maybe 401 depending on your implementation

        # Test 500 Internal Server Error (as in registration test, requires error condition simulation)


class ProfileEndpointTests(TestCase):

    def setUp(self):
        self.client = Client()
        # Assume you have a way to create a test user and get a token for authentication
        # For example, using Django's User model and some token generation logic
        # self.user = User.objects.create_user(username='testuser', password='testpassword')
        # self.token = generate_token_for_user(self.user) # Hypothetical token generation function
        self.user_id = 1 # Replace with a valid user ID for testing
        self.valid_token = "test_valid_token" # Replace with a valid token for testing

    def test_get_profile_detail(self):
        url = reverse('profile-detail', kwargs={'pk': self.user_id}) # Assuming URL name 'profile-detail'
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.valid_token}') # Include token if auth is required
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIsInstance(response_json, dict)
        self.assertIn('user', response_json)
        self.assertIn('username', response_json)
        # ... assert other fields based on example response

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.get(url)
        self.assertEqual(response_unauthorized.status_code, 401) # Or 403 depending on your auth setup

        # Test 404 Not Found
        url_not_found = reverse('profile-detail', kwargs={'pk': 9999}) # Non-existent PK
        response_not_found = self.client.get(url_not_found, HTTP_AUTHORIZATION=f'Token {self.valid_token}')
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error (as before, simulate server error in view)


    def test_patch_profile_detail(self):
        url = reverse('profile-detail', kwargs={'pk': self.user_id}) # Assuming URL name 'profile-detail'
        data = {
            "first_name": "UpdatedMax",
            "location": "New York"
        }
        response = self.client.patch(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.valid_token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertEqual(response_json['first_name'], 'UpdatedMax')
        self.assertEqual(response_json['location'], 'New York')
        # ... assert other updated fields

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.patch(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 403 Forbidden - not owner (if applicable, you might need to test permission logic)
        # Assuming you have logic to prevent users from editing others' profiles
        # ... (setup another user, try to patch their profile with the current user's token)

        # Test 404 Not Found
        url_not_found = reverse('profile-detail', kwargs={'pk': 9999})
        response_not_found = self.client.patch(url_not_found, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.valid_token}')
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


    def test_get_business_profiles_list(self):
        url = reverse('business-profiles-list') # Assuming URL name 'business-profiles-list'
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.valid_token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIsInstance(response_json, list)
        if response_json: # Check if list is not empty
            first_profile = response_json[0]
            self.assertIn('user', first_profile)
            self.assertIn('username', first_profile)
            self.assertEqual(first_profile['type'], 'business') # Verify type is business

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.get(url)
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 500 Internal Server Error


    def test_get_customer_profiles_list(self):
        url = reverse('customer-profiles-list') # Assuming URL name 'customer-profiles-list'
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.valid_token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIsInstance(response_json, list)
        if response_json:
            first_profile = response_json[0]
            self.assertIn('user', first_profile)
            self.assertIn('username', first_profile)
            self.assertEqual(first_profile['type'], 'customer') # Verify type is customer

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.get(url)
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 500 Internal Server Error


class OffersEndpointTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.valid_token = "test_valid_token" # Replace with a valid token for testing
        self.business_user_token = "business_user_token" # Token for a business user

    def test_get_offers_list(self):
        url = reverse('offer-list') # Assuming URL name 'offer-list'
        response = self.client.get(url) # No auth required according to docs
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIsInstance(response_json, dict) # Expecting paginated response
        self.assertIn('results', response_json)
        if response_json['results']:
            first_offer = response_json['results'][0]
            self.assertIn('id', first_offer)
            self.assertIn('title', first_offer)
            self.assertIn('details', first_offer)
            self.assertIsInstance(first_offer['details'], list)

        # Test query parameters (example - you should test all parameters)
        response_filtered = self.client.get(url, {'creator_id': 1}) # Assuming creator_id filtering
        self.assertEqual(response_filtered.status_code, 200)
        # ... more assertions for filtered results

        # Test 400 Bad Request - invalid query parameters (if applicable, e.g., invalid ordering value)
        response_invalid_query = self.client.get(url, {'ordering': 'invalid_field'}) # Example invalid ordering
        self.assertEqual(response_invalid_query.status_code, 400) # Or maybe 500 depending on error handling

        # Test 500 Internal Server Error


    def test_post_offers_create(self):
        url = reverse('offer-list') # Assuming URL name 'offer-list'
        data = {
            "title": "Test Offer",
            "description": "Test Description",
            "details": [
                {
                    "title": "Basic",
                    "revisions": 2,
                    "delivery_time_in_days": 5,
                    "price": 100,
                    "features": ["Feature 1", "Feature 2"],
                    "offer_type": "basic"
                }
            ]
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}') # Business user token required
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIn('id', response_json)
        self.assertEqual(response_json['title'], 'Test Offer')
        self.assertIsInstance(response_json['details'], list)
        self.assertTrue(all('id' in detail for detail in response_json['details'])) # Check if details have IDs

        # Test 400 Bad Request - missing required fields, invalid data format
        invalid_data = { # Missing title
            "description": "Test Description",
            "details": [...]
        }
        response_invalid = self.client.post(url, json.dumps(invalid_data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response_invalid.status_code, 400)

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 403 Forbidden - not business user (if enforced)
        customer_token = "customer_user_token" # Hypothetical customer token
        response_forbidden = self.client.post(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {customer_token}')
        self.assertEqual(response_forbidden.status_code, 403) # Or 401 if you just check for auth and not user type

        # Test 500 Internal Server Error


    def test_get_offer_detail(self):
        offer_id = 1 # Replace with an existing offer ID
        url = reverse('offer-detail', kwargs={'id': offer_id}) # Assuming URL name 'offer-detail'
        response = self.client.get(url) # No auth required
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIn('id', response_json)
        self.assertEqual(response_json['id'], offer_id)
        self.assertIn('title', response_json)
        self.assertIn('details', response_json)
        self.assertIsInstance(response_json['details'], list)
        self.assertTrue(all('url' in detail for detail in response_json['details'])) # Check for detail URLs

        # Test 401 Unauthorized - (docs say no auth required for GET offer detail, so this should not be 401)

        # Test 404 Not Found
        url_not_found = reverse('offer-detail', kwargs={'id': 9999})
        response_not_found = self.client.get(url_not_found)
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


    def test_patch_offer_update(self):
        offer_id = 66 # Replace with an existing offer ID for testing
        url = reverse('offer-detail', kwargs={'id': offer_id}) # Assuming URL name 'offer-detail'
        data = {
            "title": "Updated Offer Title",
            "details": [ # Example of updating details, ensure IDs match existing details
                {
                    "id": 199, # Existing detail ID
                    "title": "Basic Design Updated",
                    "revisions": 3,
                }
            ]
        }
        response = self.client.patch(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}') # Business user token
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertEqual(response_json['title'], 'Updated Offer Title')
        # ... verify details are updated as expected

        # Test 400 Bad Request - invalid data, e.g., trying to update non-editable fields
        invalid_data = {"created_at": "2025-01-24T..."} # Trying to update created_at - should be read-only
        response_invalid = self.client.patch(url, json.dumps(invalid_data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response_invalid.status_code, 400)

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.patch(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 403 Forbidden - not owner (if enforced)
        # ... (setup another business user, try to patch the offer with the current business user's token)

        # Test 404 Not Found
        url_not_found = reverse('offer-detail', kwargs={'id': 9999})
        response_not_found = self.client.patch(url_not_found, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


    def test_delete_offer(self):
        offer_id = 66 # Replace with an existing offer ID for testing
        url = reverse('offer-detail', kwargs={'id': offer_id}) # Assuming URL name 'offer-detail'
        response = self.client.delete(url, HTTP_AUTHORIZATION=f'Token {self.business_user_token}') # Business user token
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'') # Expecting no content for 204

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.delete(url)
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 403 Forbidden - not owner (if enforced)
        # ... (setup another business user, try to delete the offer with the current business user's token)

        # Test 404 Not Found
        url_not_found = reverse('offer-detail', kwargs={'id': 9999})
        response_not_found = self.client.delete(url_not_found, HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


    def test_get_offer_detail_detail(self):
        offer_detail_id = 1 # Replace with an existing offer detail ID
        url = reverse('offerdetail-detail', kwargs={'id': offer_detail_id}) # Assuming URL name 'offerdetail-detail'
        response = self.client.get(url) # No auth required
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIn('id', response_json)
        self.assertEqual(response_json['id'], offer_detail_id)
        self.assertIn('title', response_json)
        self.assertIn('price', response_json)
        self.assertIn('features', response_json)
        self.assertIsInstance(response_json['features'], list)

        # Test 401 Unauthorized - (docs say no auth required for GET offer detail detail, so this should not be 401)

        # Test 404 Not Found
        url_not_found = reverse('offerdetail-detail', kwargs={'id': 9999})
        response_not_found = self.client.get(url_not_found)
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


class OrdersEndpointTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.valid_token = "test_valid_token" # Replace with a valid token for testing
        self.customer_token = "customer_user_token" # Token for a customer user
        self.business_user_token = "business_user_token" # Token for a business user
        self.staff_token = "staff_user_token" # Token for a staff user

    def test_get_orders_list(self):
        url = reverse('order-list') # Assuming URL name 'order-list'
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.valid_token}') # Auth required
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIsInstance(response_json, list)
        if response_json:
            first_order = response_json[0]
            self.assertIn('id', first_order)
            self.assertIn('customer_user', first_order)
            self.assertIn('business_user', first_order)
            self.assertIn('status', first_order)

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.get(url)
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 500 Internal Server Error


    def test_post_orders_create(self):
        url = reverse('order-list') # Assuming URL name 'order-list'
        data = {
            "offer_detail_id": 1 # Replace with an existing offer detail ID
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.customer_token}') # Customer token required
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIn('id', response_json)
        self.assertIn('customer_user', response_json)
        self.assertIn('business_user', response_json)
        self.assertIn('status', response_json)
        self.assertEqual(response_json['status'], 'in_progress') # Default status

        # Test 400 Bad Request - missing offer_detail_id, invalid offer_detail_id
        invalid_data = {} # Missing offer_detail_id
        response_invalid = self.client.post(url, json.dumps(invalid_data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.customer_token}')
        self.assertEqual(response_invalid.status_code, 400)

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 403 Forbidden - not customer user (if enforced)
        response_forbidden = self.client.post(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}') # Business user token
        self.assertEqual(response_forbidden.status_code, 403) # Or 401 if only auth is checked

        # Test 404 Not Found - invalid offer_detail_id
        not_found_data = {"offer_detail_id": 9999}
        response_not_found = self.client.post(url, json.dumps(not_found_data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.customer_token}')
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


    def test_patch_order_update_status(self):
        order_id = 1 # Replace with an existing order ID
        url = reverse('order-detail', kwargs={'id': order_id}) # Assuming URL name 'order-detail'
        data = {
            "status": "completed"
        }
        response = self.client.patch(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}') # Business user token
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertEqual(response_json['status'], 'completed')

        # Test 400 Bad Request - invalid status value
        invalid_data = {"status": "invalid_status"}
        response_invalid = self.client.patch(url, json.dumps(invalid_data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response_invalid.status_code, 400)

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.patch(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 403 Forbidden - not business user (if enforced for status update) or not owner (if owner check)
        customer_token = "customer_user_token" # Hypothetical customer token
        response_forbidden = self.client.patch(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {customer_token}')
        self.assertEqual(response_forbidden.status_code, 403) # Or 401

        # Test 404 Not Found
        url_not_found = reverse('order-detail', kwargs={'id': 9999})
        response_not_found = self.client.patch(url_not_found, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


    def test_delete_order_staff_only(self):
        order_id = 1 # Replace with an existing order ID
        url = reverse('order-detail', kwargs={'id': order_id}) # Assuming URL name 'order-detail'
        response = self.client.delete(url, HTTP_AUTHORIZATION=f'Token {self.staff_token}') # Staff token
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.delete(url)
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 403 Forbidden - not staff user
        response_forbidden_customer = self.client.delete(url, HTTP_AUTHORIZATION=f'Token {self.customer_token}')
        self.assertEqual(response_forbidden_customer.status_code, 403)
        response_forbidden_business = self.client.delete(url, HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response_forbidden_business.status_code, 403)

        # Test 404 Not Found
        url_not_found = reverse('order-detail', kwargs={'id': 9999})
        response_not_found = self.client.delete(url_not_found, HTTP_AUTHORIZATION=f'Token {self.staff_token}')
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


    def test_get_order_count_in_progress(self):
        business_user_id = 2 # Replace with an existing business user ID
        url = reverse('order-count-in-progress', kwargs={'business_user_id': business_user_id}) # Assuming URL name 'order-count-in-progress'
        response = self.client.get(url) # No auth required
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIn('order_count', response_json)
        self.assertIsInstance(response_json['order_count'], int)

        # Test 401 Unauthorized - (docs say no auth required for GET order count, so this should not be 401)

        # Test 404 Not Found - business user not found
        url_not_found = reverse('order-count-in-progress', kwargs={'business_user_id': 9999})
        response_not_found = self.client.get(url_not_found)
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


    def test_get_order_count_completed(self):
        business_user_id = 2 # Replace with an existing business user ID
        url = reverse('order-count-completed', kwargs={'business_user_id': business_user_id}) # Assuming URL name 'order-count-completed'
        response = self.client.get(url) # No auth required
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIn('completed_order_count', response_json)
        self.assertIsInstance(response_json['completed_order_count'], int)

        # Test 401 Unauthorized - (docs say no auth required for GET completed order count, so this should not be 401)

        # Test 404 Not Found - business user not found
        url_not_found = reverse('order-count-completed', kwargs={'business_user_id': 9999})
        response_not_found = self.client.get(url_not_found)
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


class ReviewsEndpointTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.valid_token = "test_valid_token" # Replace with a valid token for testing
        self.customer_token = "customer_user_token" # Token for a customer user

    def test_get_reviews_list(self):
        url = reverse('review-list') # Assuming URL name 'review-list'
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.valid_token}') # Auth required
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIsInstance(response_json, list)
        if response_json:
            first_review = response_json[0]
            self.assertIn('id', first_review)
            self.assertIn('business_user', first_review)
            self.assertIn('reviewer', first_review)
            self.assertIn('rating', first_review)

        # Test query parameters (example - you should test all parameters)
        response_filtered = self.client.get(url, {'business_user_id': 2}, HTTP_AUTHORIZATION=f'Token {self.valid_token}') # Filter by business user
        self.assertEqual(response_filtered.status_code, 200)
        # ... more assertions for filtered results

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.get(url)
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 500 Internal Server Error


    def test_post_reviews_create(self):
        url = reverse('review-list') # Assuming URL name 'review-list'
        data = {
            "business_user": 2, # Replace with an existing business user ID
            "rating": 4,
            "description": "Test Review Description"
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.customer_token}') # Customer token required
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIn('id', response_json)
        self.assertEqual(response_json['business_user'], 2)
        self.assertEqual(response_json['rating'], 4)
        self.assertEqual(response_json['description'], 'Test Review Description')
        self.assertIn('reviewer', response_json) # Reviewer should be the current user

        # Test 400 Bad Request - missing fields, invalid rating, duplicate review
        invalid_data = { # Missing business_user
            "rating": 4,
            "description": "Test Review Description"
        }
        response_invalid = self.client.post(url, json.dumps(invalid_data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.customer_token}')
        self.assertEqual(response_invalid.status_code, 400)

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 403 Forbidden - not customer user (if enforced) or duplicate review
        business_user_token = "business_user_token" # Hypothetical business user token
        response_forbidden = self.client.post(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {business_user_token}')
        self.assertEqual(response_forbidden.status_code, 403) # Or 401 if only auth is checked

        # Test 500 Internal Server Error


    def test_patch_review_update(self):
        review_id = 1 # Replace with an existing review ID created by the test user
        url = reverse('review-detail', kwargs={'id': review_id}) # Assuming URL name 'review-detail'
        data = {
            "rating": 5,
            "description": "Updated Review Description"
        }
        response = self.client.patch(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.customer_token}') # Customer token (reviewer token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertEqual(response_json['rating'], 5)
        self.assertEqual(response_json['description'], 'Updated Review Description')

        # Test 400 Bad Request - invalid data, e.g., trying to update non-editable fields
        invalid_data = {"business_user": 3} # Trying to change business_user - should be forbidden
        response_invalid = self.client.patch(url, json.dumps(invalid_data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.customer_token}')
        self.assertEqual(response_invalid.status_code, 400)

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.patch(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 403 Forbidden - not reviewer (owner)
        business_user_token = "business_user_token" # Hypothetical token of a user who is not the reviewer
        response_forbidden = self.client.patch(url, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {business_user_token}')
        self.assertEqual(response_forbidden.status_code, 403) # Or 401

        # Test 404 Not Found
        url_not_found = reverse('review-detail', kwargs={'id': 9999})
        response_not_found = self.client.patch(url_not_found, json.dumps(data), content_type='application/json', HTTP_AUTHORIZATION=f'Token {self.customer_token}')
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


    def test_delete_review(self):
        review_id = 1 # Replace with an existing review ID created by the test user
        url = reverse('review-detail', kwargs={'id': review_id}) # Assuming URL name 'review-detail'
        response = self.client.delete(url, HTTP_AUTHORIZATION=f'Token {self.customer_token}') # Customer token (reviewer token)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')

        # Test 401 Unauthorized - no token
        response_unauthorized = self.client.delete(url)
        self.assertEqual(response_unauthorized.status_code, 401)

        # Test 403 Forbidden - not reviewer (owner)
        business_user_token = "business_user_token" # Hypothetical token of a user who is not the reviewer
        response_forbidden = self.client.delete(url, HTTP_AUTHORIZATION=f'Token {business_user_token}')
        self.assertEqual(response_forbidden.status_code, 403) # Or 401

        # Test 404 Not Found
        url_not_found = reverse('review-detail', kwargs={'id': 9999})
        response_not_found = self.client.delete(url_not_found, HTTP_AUTHORIZATION=f'Token {self.customer_token}')
        self.assertEqual(response_not_found.status_code, 404)

        # Test 500 Internal Server Error


class BaseInfoEndpointTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_get_base_info(self):
        url = reverse('base-info') # Assuming URL name 'base-info'
        response = self.client.get(url) # No auth required
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        response_json = response.json()
        self.assertIn('review_count', response_json)
        self.assertIn('average_rating', response_json)
        self.assertIn('business_profile_count', response_json)
        self.assertIn('offer_count', response_json)
        self.assertIsInstance(response_json['review_count'], int)
        self.assertIsInstance(response_json['average_rating'], float)
        self.assertIsInstance(response_json['business_profile_count'], int)
        self.assertIsInstance(response_json['offer_count'], int)

        # Test 500 Internal Server Error


