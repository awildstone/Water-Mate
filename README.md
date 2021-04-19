# Water-Mate
Water Mate helps you organize your collection of houseplants and manage their watering schedule.

### Capstone 1 Proposal  - Water Mate

### 1. What goal will your website be designed to achieve? 

Water Mate will manage the watering schedule for houseplant lovers by organizing their collection of houseplants by location and remind the user when it’s time to water their plant in a daily digest.

### 2. What kind of users will visit your site? In other words, what is the demographic of your users?

Any person around the world who enjoys caring for houseplants can use this app. Any person who can identify the type of plant they have and can enter the details about the plant location and light source in their home can use this app.

### 3. What data do you plan on using? You may have not picked your actual API yet, which is fine, just outline what kind of data you would like it to contain.

The app will use the user’s geolocation to collect data about the amount of daily sunlight in the user’s geolocation. This data is used to formulate a recommended watering schedule for a plant, based on the plant’s type, location near a light source, amount of light, and the type of light source.

The location of the user determines the daily potential of sunlight a plant can receive and the type of light source in that user’s location determines the quantity of light a plant receives.

For example, in the northern hemisphere, south-facing windows receive the most light exposure while north-facing windows receive the least. East-facing windows receive cooler morning exposure and western windows receive hotter afternoon exposure. There is less potential sunlight in winter vs summer months due to the angle of the sun rise/set.

This app will not include the calculation of the sun’s angle in the first iteration but will likely include this in a later release to improve the watering algorithm. Future releases can also include other important local environmental factors such as cloud cover and temperature.

The database will contain a list of general plant categories along with help for the user to choose a category for their plant. The category will contain the base watering recommendation that will be altered using data on the amount and quality of light the plant receives. I will likely scrape this data from a few websites.

Potential Websites for scraping general data for a base watering schedule:
* [https://www.ourhouseplants.com/sitemap#plants](https://www.ourhouseplants.com/sitemap#plants)
* [https://osera.org/](https://osera.org/)

I will be using mapquest to generate a user's lat/long location coordinates based off of the user's city/state/zip that they enter:
* https://developer.mapquest.com/

I will use this free API to get the daily amount of sunlight in a user's location for a given day (I could potenitally use other data from this API in the future):
* [https://sunrise-sunset.org/api](https://sunrise-sunset.org/api)

In future iterations I can potentially use a service like Sun-Calc to get the angle of the sun for a given time of year:
* [https://www.suncalc.org/](https://www.suncalc.org/)

I have also considered future iterations could get lat/long data from the user's ip address, or allow the user to manually enter their city/state/zip for better accuracy:
* [https://ip-api.com/](https://ip-api.com/)

### 4. In brief, outline your approach to creating your project (knowing that you may not know everything in advance and that these details might change later). Answer questions like the ones below, but feel free to add more information:
 
#### a. What does your database schema look like? 

Starting schema mockup here:
[https://app.quickdatabasediagrams.com/#/d/mxfbkG](https://app.quickdatabasediagrams.com/#/d/mxfbkG) 


#### b. What kinds of issues might you run into with your API?

I could run into issues if the API I used to get sun calculations goes down or in the future local weather/temps. This could affect the recommended watering algorithm calculations if I am not storing this data.

I will need to make a decision on how often to update environmental variables in the future, but for now, I can simply gather the sunlight data for a user’s location each time a plant's watering schedule is updated, or if a user updates their location.


#### c. Is there any sensitive information you need to secure?

Yes - user’s name, email, password, and the user’s lat and long geolocation variables. To protect users my app will only ask for the user’s City, State, Zipcode to calculate these variables and store them. I will be cryptographically hashing and salting the passwords.


#### d. What functionality will your app include?

Users can update their user profile information such as name, email, password, or update/reset their geolocation using their country/city. Users will not be able to update their username. For now, all user's will have Owner (Admin) user permissions over their account. 
(Future iterations will give Owners the ability to add a Caregiver (User) role access to their account if they need someone else to manage the watering schedule on their behalf. The Admin user can add or remove this user's access in their account at any time and the Caregiver role will only have ability to view collection or add notes, mark a plant watered, or snooze the plant water schedule.)

Users will have a “collection” where they can view, add, edit, or delete rooms. Users can have multiple collections (such as Home and Office).

Rooms help organize a plant collection and describe the location of the plant. Rooms will have light sources such as North, South, East, or West facing windows or artificial light sources. Light sources in rooms can be added, edited, or deleted.

Users will add plants to their collection. Each plant will have a name, photo, plant type, room location, light source, and a watering schedule. The User will provide a plant name and optional photo and the user will select a type from a table, the room from a dropdown, lightsource from dropdown. The app will create and calculate the plant's water schedule using this data.

The watering schedule can be modified for a specific plant. The watering schedule is calculated using the amount of daily light in the user’s geolocation, the location of the plant to a light source, and the type of plant.

#### e. What will the user flow look like?

A user will register their account information including name, email, username, password, and City/State/Zip. City/State/Zip will be used to calculate and store user’s geolocation.

The user will be greeted with a landing page of instructions to get started. The instructions will include how to access the user controls in navigation and a brief intro of how the app works. Users will be able to access all of this info on an "About" tab at any time if they need to reference.

Users will be instructed to create the rooms in their home first, then add room light sources, then add plants. Users cannot add a plant without being able to select a room and light source (from a dropdown generated by user data).

Users can modify room names or delete rooms from the Collection view. Users cannot delete rooms that have plants and will be warned to update the plant location first.

From a Room view, users can modify or delete light sources and view a list of all of the plants in a room. Users will receive an error if they try to delete a light source that has plants (those plants need to be moved).

From the plant view, users can modify the plant name, photo, location, light source, type, or delete the plant if it died. The user also will have controls in the watering schedule table.

The watering schedule history table will show the date the plant was last marked watered by the user, snooze data (if any), any notes the user may have added, the current calculated water timeline (eg, every 7 days), and the upcoming watering date. The history table will be limited the 20 most recent events, after this, user's can request a history report to view past events. (Future iterations may include pagination of history table).

Notes are optional for a user to add - eg saw pests, needs fertilizer, the soil was still very moist or too dry, etc. 

Users can manually adjust the calculated water timeline if it is not meeting their needs increasing or decreasing the number of days between waterings. The app will respect manual overrides and ignore this row for algorithmic updates, and the watering table will somehow indicate to the user that it is set to manual mode. The user can also “reset” the watering timeline to the app’s algorithmic recommendations if they want to resume.

A daily digest page will include all of the plants the user needs to water that day. The user will receive a reminder via email link that takes them directly to the daily digest view. When the user marks a plant watered in the daily digest table, this will update the watering table data in the plant view.

Users can also “snooze” a plant on the watering schedule from the daily digest page for 1, 3, or 7 days. Snoozing effectively adjusts the “next watering date” without adjusting the plant’s current water timeline and a user can leave a note as to why the plant was snoozed. The user will be reminded again to water the plant after the snooze period has elapsed.

Lastly, users can generate a report of plant care from the plant page that will include all water events and notes for a specific timeline (or all time). This report will be emailed to the user.

#### f. What features make your site more than CRUD? Do you have any stretch goals?

This app will have a watering algorithm that calculates a watering schedule based on input from the user such as the location and type of plant, and external environmental factors such as the user’s location on earth and the time of year.

This app will include a daily digest of plants to water that is interactive and adjustable for the user.

This app will include custom reporting data available to the user, in cases where they want to evaluate the effectiveness of a watering timeline, track health issues, or learn why a plant may have died.
