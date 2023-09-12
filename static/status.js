
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

// status box change color
function changeColor2(e) {
  if (e.value === 1) {
    e.style.backgroundColor = 'green'; // Change to your desired color
  } else if (e.value === 2) {
    e.style.backgroundColor = 'yellow'; // Change to your desired color
  } else if (e.value === 3) {
    e.style.backgroundColor = 'orange'; // Change to your desired color
  } else if (e.value === 4) {
    e.style.backgroundColor = 'red'; // Change to your desired color
  }
}
