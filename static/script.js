window.addEventListener('DOMContentLoaded', function() {
    // Your existing code here

    window.addEventListener('error', function(event) {
        console.error('JavaScript error:', event.error);
    });
});

// Rest of your script code...



window.addEventListener('DOMContentLoaded', function() {
    let checkboxes = document.querySelectorAll('input[type="checkbox"]');
    let recipientInput = document.getElementById('recipients');

    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            let recipients = Array.from(checkboxes)
                .filter(function(checkbox) {
                    return checkbox.checked;
                })
                .map(function(checkbox) {
                    return checkbox.value;
                });

            recipientInput.value = recipients.join(',');
        });
    });
});


// Execute the code after the DOM content has loaded
document.addEventListener('DOMContentLoaded', function() {
    let checkboxes = document.querySelectorAll('.contact-checkbox');
    let selectAllBtn = document.querySelector('.select-all');

    if (checkboxes.length > 0 && selectAllBtn) {
        // Add event listener to the "Select All" checkbox
        selectAllBtn.addEventListener('change', toggleAllContacts);
    } else if (selectAllBtn) {
        // Hide the "Select All" checkbox if no contact checkboxes exist
        selectAllBtn.setAttribute('style', 'display: none');
    }

    console.log(selectAllBtn); // Add this line

});

window.addEventListener('load', function() {
    let textarea = document.getElementById("message");
    let storedMessage = localStorage.getItem("message");
    let urlMessage = "{{ request.args.get('message', '') }}";

    if (textarea) {
      if (storedMessage) {
        textarea.value = storedMessage;
      } else if (urlMessage && urlMessage !== "") {
        let decodedMessage = decodeURIComponent(urlMessage);
        textarea.value = decodedMessage;
        localStorage.setItem("message", decodedMessage);
      } else {
        textarea.value = "";
      }
    }
});

function toggleAllContacts() {
    let checkboxes = document.querySelectorAll(".contact-checkbox");
    let selectAllBtn = document.getElementById("select-all-btn");
    let selectAllLabel = document.getElementById('select-all-label');

    let selectAll = !selectAllBtn.checked;

    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAll;
    });

    if (selectAllBtn.checked) {
        selectAllLabel.textContent = 'Deselect All';
    } else {
        selectAllLabel.textContent = 'Select All';
    }
}


