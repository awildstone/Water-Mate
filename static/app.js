const BASE_URL = 'http://127.0.0.1:5000/water-manager/';

/* Selector for the Edit Water Schedule form and Watering Interval Formfield
If the box is checked, shows the field. If the box is not checked hides the field. */

const checkbox = document.getElementById('manual_mode');
const formField = document.getElementById('water_interval_field');

if (checkbox) {
    //On window load toggle or hide the form field.
    window.addEventListener('load', function() {
        if (checkbox.checked) {
            formField.style.display = 'block';
        } else {
            formField.style.display = 'none';
        }
    });

    checkbox.addEventListener('change', function() {
        if (checkbox.checked) {
            formField.style.display = 'block';
        } else {
            formField.style.display = 'none';
        }
    });
}

/* Selector for the Card Elements container.
If the "Add Notes" button is clicked show the "Add Notes" form.
If the "Add Notes" button is clicked again, hide the form. */

const container = document.getElementById('plants_container');

if (container) {
    container.addEventListener('click', function(e) {
        let target = e.target;
        if (target.classList.contains('notes_btn')) {
            form = target.nextSibling;
            if (form.style.display === 'none') {
                form.style.display = 'inline';
            } else {
                form.style.display = 'none';
            }
        }
    });
}

/* Selectors for the Water and Snooze buttons.
Clicking the Water button will submit a request to the server to water the plant and include notes for the water history (if any).
Clicking the snooze button will submit a request to the server to snooze a plant and include notes for the water history (if any). */

const waterButton = document.getElementById('water_button');
const snoozeButton = document.getElementById('snooze_button');

/* Checks which button triggered the form submit. */
if (container) {
    container.addEventListener('click', function(e) {

        if (e.target.getAttribute('name') ===  'water_button') {
            let plant_id = e.target.getAttribute('data-plant-id');
            let notes = document.querySelector('textarea').value
            waterPlant(plant_id, notes);
        }
        if (e.target.getAttribute('name') ===  'snooze_button') {
            let plant_id = e.target.getAttribute('data-plant-id');
            let notes = document.querySelector('textarea').value
            snoozePlant(plant_id, notes);
        }
    });
}

/* Makes a call to the API to water a plant. */
async function waterPlant(plant_id, notes) {
    // send post request to server
    response = await axios.post(`${BASE_URL}${plant_id}/water`, {"notes": notes});
    console.log(response.status)
    if (response.status === 201) {
        // remove the updated plant from the dashboard
        let card = document.querySelector(`div[data-col-id='${plant_id}']`);
        card.remove();
    }
}

/* Makes a call to the API to snooze a plant's water schedule. */
async function snoozePlant(plant_id, notes) {
    // send post request to server
    response = await axios.post(`${BASE_URL}${plant_id}/snooze`, {"notes": notes});
    console.log(response.status)
    if (response.status === 201) {
        // remove the updated plant from the dashboard
        let card = document.querySelector(`div[data-col-id='${plant_id}']`);
        card.remove();
    }
}