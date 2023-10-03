
// functin to directly calculate the time difference between start time and end 
function calculateTimeDifference() {
  const startTimeInput = document.getElementById('start_time');
  const endTimeInput = document.getElementById('end_time');
  const timeDifferenceOutput = document.getElementById('time_difference');

  const startStr = startTimeInput.value;
  const endStr = endTimeInput.value;

  // Parse the times and calculate the difference
  const startTime = parseTime(startStr);
  const endTime = parseTime(endStr);

  if (startTime && endTime) {
    // Calculate the time difference in milliseconds
    let timeDifference = endTime - startTime;

    // Handle negative time differences (crossing over midnight)
    if (timeDifference < 0) {
      timeDifference += 24 * 60 * 60 * 1000; // Add 24 hours in milliseconds
    }

    // Convert the time difference to hours and minutes
    const hours = Math.floor(timeDifference / (60 * 60 * 1000));
    const minutes = Math.floor((timeDifference % (60 * 60 * 1000)) / (60 * 1000));

    timeDifferenceOutput.textContent = `Time Difference: ${hours} hours and ${minutes} minutes`;
  } else {
    timeDifferenceOutput.textContent = '';
  }
}

function parseTime(timeStr) {
  const [hours, minutes] = timeStr.split(':').map(Number);
  if (!isNaN(hours) && !isNaN(minutes)) {
    return hours * 60 * 60 * 1000 + minutes * 60 * 1000;
  }
  return null;
}

// JavaScript to open the time logging pop-up
function openTimeLogPopup() {
  document.getElementById("timeLogPopup").style.display = "block";
}

// JavaScript to close the time logging pop-up
function closeTimeLogPopup() {
  document.getElementById("timeLogPopup").style.display = "none";
}