
// status box change color
function changeColor(e) {
  if (e.value === "not_started") {
    e.style.backgroundColor = 'grey'; // Change to your desired color
  } else if (e.value === "inprogress") {
    e.style.backgroundColor = 'CadetBlue'; // Change to your desired color
  } else if (e.value === "completed") {
    e.style.backgroundColor = 'green'; // Change to your desired color
  }
}

// Get the "Priority" dropdown element by its ID
const priorityDropdown = document.getElementById('priority_level');

// Function to change the class of the "Priority" dropdown based on the selected option
function changePriorityColor() {
    const selectedOption = priorityDropdown.options[priorityDropdown.selectedIndex];
    const priorityValue = selectedOption.value;

    // Remove any existing priority class
    priorityDropdown.className = '';

    // Add the appropriate priority class based on the selected value
    switch (priorityValue) {
        case '1':
            priorityDropdown.classList.add('low-priority');
            break;
        case '2':
            priorityDropdown.classList.add('medium-priority');
            break;
        case '3':
            priorityDropdown.classList.add('important-priority');
            break;
        case '4':
            priorityDropdown.classList.add('urgent-priority');
            break;
        default:
            // Handle the default case here (if needed)
            break;
    }
}

// Add an event listener to the "Priority" dropdown to call the function when it changes
priorityDropdown.addEventListener('change', changePriorityColor);

// Call the function initially to set the initial color based on the default selected option
changePriorityColor();



