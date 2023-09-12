
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

// Get all the table cells by their class or ID
const cells = document.querySelectorAll('.custom-table td');

// Loop through each cell and change the background color based on content
cells.forEach(cell => {
    const content = cell.textContent.toLowerCase();
        
    // Example: Change the color for specific content
    if (content.includes(4)) {
        cell.style.backgroundColor = 'red';
        cell.style.color = 'white';
    } else if (content.includes(3)) {
        cell.style.backgroundColor = 'orange';
    } else if (content.includes(2)) {
        cell.style.backgroundColor = 'yellow';
    } else if (content.includes(1)) {
        cell.style.backgroundColor = 'green';
    }
});

// status box change color
// function changeColor2(e) {
//   if (e.value === '1') {
//     e.style.backgroundColor = 'green'; // Change to your desired color
//   } else if (e.value === '2') {
//     e.style.backgroundColor = 'yellow'; // Change to your desired color
//   } else if (e.value === '3') {
//     e.style.backgroundColor = 'orange'; // Change to your desired color
//   } else if (e.value === '4') {
//     e.style.backgroundColor = 'red'; // Change to your desired color
//   }
//   else {
//     e.style.backgroundColor = 'white';
//   }
// }
