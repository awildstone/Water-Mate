# [Water Mate](https://water-mate.herokuapp.com/)


### Technologies used
Water Mate is a full stack Python application built on the Flask serverside framework and uses Flask-SQLAlchemy, Flask-WTForm, Postgres database, and [S3 (Boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html) for persisting user uploads and data. 

The app is styled using the Bootstrap frontend framework, Jinja HTML templates, and JavaScript (Axios) for client AJAX requests.

* The app is hosted on Heroku. You can visit and try out the live production app: [https://water-mate.herokuapp.com/](https://water-mate.herokuapp.com/)
* Geolocation data is gathered using [Mapquest Geocoding API](https://developer.mapquest.com/documentation/geocoding-api/).
* Solar Data  is generated using the [Sunset and Sunrise times API.](https://sunrise-sunset.org/api)
* Database schema: [https://app.quickdatabasediagrams.com/#/d/mxfbkG](https://app.quickdatabasediagrams.com/#/d/mxfbkG) 

###How to setup the local enviroment to contribute
If you are interested in contributing you can create a pull request then you will need the following in your environment:

1. Python 3.9.2 - create a venv and pip3 install requirements.txt
2. Create a .env file to manage environment variables.
3. You will need to sign up for a [Mapquest API key](https://developer.mapquest.com/plan_purchase/steps/business_edition/business_edition_free/register) and add MAPQUEST_KEY=your-key to the .env file
4. The S3 user uploads feature cannot work without a configured S3 bucket. You will need to set up your own free S3 account and [configure the bucket to public](https://aws.amazon.com/premiumsupport/knowledge-center/read-access-objects-s3-bucket/). You will need to add variables to .env for AWS\_ACCESS\_KEY\_ID, AWS\_SECRET\_ACCESS\_KEY, S3\_BUCKET (your bucket name), and S3\_LOCATION (the direct URL to your objects ending with /uploads/user/ to match the path on the app).
5. Set up a Postres database called **water_mate**, then run Seed.py to setup the DB tables and seed with the required LightType and PlantType data.
6. /static/app.js contains urls for making AJAX calls to the server. Make sure the BASE\_URL is set to your local server.


### How this app works

Water Mate helps houseplant lovers organize their houseplants into Collections with Rooms, Lightsources, and Plants and reminds the user when it’s time to water their plant. Any person around the world who loves houseplants and can identify the type of plant they own can use this app.

#####Signup & Configuration
A user can sign up in one step and begin using the app right away:

* The user's geolocation is generated on signup, then the user is directed to the Getting Started page to learn how to use the app. The Getting Started page includes how to get started using the app, and tips for success. Users will be able to access all of this info on an "Get Started" tab at any time if they need to reference.
* All controlls are hidden until a user adds their first Collection by name.
* Users will be instructed to create the rooms, then add room lightsources, then add plants. Controls are made visible in order to control the users flow through the setup.
* From a Room view, users can modify or delete light sources and view a list of all of the plants in a room. Users will receive an error if they try to delete a room or lightsource that has plants.
* From the plant view, users can modify the plant name, photo, location, light source, type, or delete the plant if it died. The user also will have controls to update the water schedule or view the plant's water history.


Once the configuration is complete, the user can visit the Dashboard to manage their Collection(s) or visit the Water Manager to care for their plants.

#####User Features
* Users can add, edit, or delete Collections, Rooms, and Plants as needed to keep their collection details current. Users cannot delete Collections or Rooms that have plants in them and will recieve a warning if attempting to do so (because they need to delete or move the plant first). Users can create and manage multiple Collections.
* Rooms help organize a plant collection and describe the location of the plant. Rooms will have lightsources such as North, South, East, or West facing windows or artificial lightsources. Lightsources in rooms can be added, edited, or deleted.
* Each plant will have a name, photo, plant type, lightsource, collection location, room location, water schedule details, and water history. The User will provide a plant name and optional photo and the user will select a type and lightsource from available dropdown. All of the plant's details can be viewed or managed from the plant detail view page.
* Users can water a plant or snooze a plant's watering schedule in the Water Manager.
* Watering a plant will trigger the water algorithm to generate a new water date for the plant. If the water schedule is set to manual mode or the plant's lightsource is artificial the water algorithm will not be used and the next water date is updated using the water interval.
* Snoozing a plant adjusts the plant's water schedule for three days but does not updte the last water date. This feature is helpful if a plan't soil is too moist and not ready to water yet.
* Users can add notes to water events (Water or Snooze) to indicate care details about the plant (soil too dry or wet, pest prevention, fertilized, ect.).
* Users can modify the water interval for a plant, or set a plant's water schedule to a manual water interval (for cases where the environment is controlled with artificial light and seasonal adjustments are not needed).
* Users can view a plant's history seeing all of the past care events (Water or Snooze) and notes (if any). Helpful for determining if a water schedule needs correction or trying to understand why a plant may have died.
* Users can update their profile details, update their password, and even update their geolocation if needed.
* Users can delete their account and all data (including uploads) if they choose to no longer use the app.

#####Water Algorithm
When a user signs up for an account, the user's geolocation (latitude and longitude) is captured and used by the Water Mate watering algorithm to calculate a watering schedule unique to each plant. The water algorithm is composed of a location, plant type data, light type data, a solar calculator, and a water calculator. The algorithm will start working for a plant as soon as it is added to the app.

#####Solar Calculator
The Solar Calculator uses a solar data API, a user's geolocation data, and a plant water interval (the number of days between watering) to calculate a solar forcast. 

* The solar forcast contains the maximum amount of daily light a plant recieves with consideration of the plant's light source type and location on earth. 
* For example, in the northern hemisphere, south-facing windows receive the most light exposure while north-facing windows receive the least. East-facing windows receive morning exposure from sunrise to solar noon, and western windows receive afternoon exposure from solar noon to sunset. There is less daily sunlight in winter vs. more daily light summer seasons due to the angle of the sun in the user's location. 
* These considerations are taken into account when calculating the maximum amount of light a plant recieves each day during the water interval period.

#####Water Calculator
The Water Calculator calculates a water interval for a single plant and determines the plant's next water date.

* The Water Calculator uses data about the plant's base care requirements, and the solar forcast's daily maximum light potential for each day in the days between watering the plant (the water interval). 
* The max daily light from the solar forcast is averaged over the total number of days in the water interval. The plant type base light requirements are subtracted from the average amount of light the plant recieves.
* A negative result indicates that a plant is recieving (on average) less light than it needs to thrive, therefore the water interval should increase to avoid over-watering the plant.
* A positive result indicates that the plant is recieving (on average) enough or more than enough light and the water interval should decrease for more frequent watering.
* The result of the (average light) - (base light requirements) is compared to a threshold that calculates how much of an adjustment to make to the water interval. When the differences are smaller minor adjustments are made, and larger differences will make larger adjustments in an attempt to correct/compensate. 
* The reason for this is because plants using natural light will experience changes depending on the season, therefore minor adjustments need to be made throughout the year to account for the changes in light. Plants living in poor conditions (not enough light, or too much) need corrections made to the care routine immediately as the initial base care requirements for the plant type assumes the plant lives in optimal conditions when it is first added to the app.

#####Other considerations in this algorithm:
1. Sometimes a home cannot provide ideal light conditions for the plant's type no matter what and the watering algorithm could continue to adjust the schedule due to poor conditions. Therefore, a max-days-without-water threshold is set by the algorithm with the max-days-without-water coming from the plant type base care data.

2. Sometimes the algorithm may attempt to make a correction or extreme correction that may set the water interval to a negative number. In this case the algorithm will "reset" the water interval to 3 days and then the user can check the plant's condition and Water or Snooze accordingly in 3 days.

3. No matter what, the water interval will never exceed the plant type max-days-without-water so plants in less than optimal conditions will recieve enough water to stay alive and plants in extreme conditions will not recieve too much water so as to cause root rot.

###Improvements

Water Mate does not yet account for important enviromental factors that will affect how often to water a plant such as trees or structures blocking a lightsource, cloud cover, local temperature, or local humidity. I have a few ideas on how to compensate for these factors to improve the water algorithm:

1. Adding a modifier of some kind to light sources that users can add to indicate obstructions. The modifier can indicate some kind of severity where 1 is mildly obstructed and 5 is fully obstructed. These modifiers can be used in the Solar Calculator to modify the max-daily-light further.

2. In a similar fashion, the algorithm could improve to use a weather API to gather data on average temperature and cloudcover. Modifiers can be used for temperature (higher temps = more water, lower temps = less water) and cloudcover can modify the total amount of light a plant recieves.

3. If there are APIs that offer data about local humidity using geolocation I would love to hear about it! This is a tough problem because people's homes vary greatly on how much humidity there is.

4. I would like to also evevtually improve the accuracy of the Solar Calculator by including calculations of the sun's azimuth. Modifiers should be used to account for the azimuth in the user's locality as this will affect how much direct sunlight can reach a plant in winter vs. summer months. I found this API that would be extremely helpful if I can find a way to use the data: [https://www.suncalc.org/](https://www.suncalc.org/)

5. I would like to implement a feature that emails the user a link to login when they have plants ready to water in their Water Manager view. When returning users log in they are automatically directed to the Water Manager view.

6. I would like to grant Collection owners the ability to add Caretaker roles temporarily. The Collection owner could manage this user account by creating, updating permissions, or deleting the account. The Caretaker role could only have access to Water and Snooze plants in the Water Manager view (and add notes), or be granted ability to view the dashboard but not have any edit capabilities.

7. I would like to build a feature that exports all data (in a CSV) about a plant or all plants in the collection.

8. [I have a doc of feature improvements that I will update as more ideas come to me and others deployed.](https://docs.google.com/document/d/12R3ovz82NcN3S5h0J6SjgOv-kATnyncojOORNjq90GU/edit?usp=sharing)

###Questions/Feedback?

I would love questions, or feedback on how I can improve. This app is far from perfect and I want to learn how I can make it better. Please contact me awildstone@gmail.com
