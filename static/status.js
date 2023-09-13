
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

