# Django Rest Framework API project
  
### Part 1: Get it working  
This is a vanilla Django Rest Framework application. There are issues with the application which you will need to find and fix before you can move onto part two.  The application needs to be functional when completed. 
  
### Part 2: Managing users  
Currently, our application doesn't allow users to be added or deleted through the API. 
* Only staff users should be able to do this
* If someone deletes a user it should "soft delete", so instead of removing the record from the database it should simply be flagged as deleted.
* If a user is deleted it should be filtered from all views of any non-staff user
* If the user is staff the app should optionally display deleted users when they specify a flag to the api endpoint
* Make sure the user is able to be interacted with in the Django admin.
* This system needs to have tests.

### Part 3: Audit Log  
We are interested in seeing what was done in the system.  To this end we would like you to add a new feature which will store all API actions and allow us to view them through another API endpoint.

Requirements for the model:
* The action should be stored in the database
* It should have the user attached
* The model should record the model name, id, action taken (update, create, destroy), and timestamp
* Should only be visible to Staff.  No one should be able to add or edit through the API
* Add the model to the django admin
* Tests should be included

### Part 4: Authentication
We need to make sure people can use our API programmatically so we need to make sure the API will accept tokens.

* Ensure that the API can accept both django login as well as token login
* The API needs to have the urls set up for the token retrieval
