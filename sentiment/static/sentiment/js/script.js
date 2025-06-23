const textarea = document.getElementById("text");

    textarea.addEventListener("input", function () {
        this.style.height = "auto"; // Reset height
        this.style.height = this.scrollHeight + "px"; // Set new height
    });


        // Get all tab elements
        const tabs = document.querySelectorAll('.tab');
    
        // Add click event listener to each tab
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tab
            tab.classList.add('active');
            
            // Hide all tab content
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Show the corresponding tab content
            const tabId = tab.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            });
        });

        // function saveChoice() {
        //     const selectedOption = document.querySelector('input[name="option"]:checked');
        //     if (selectedOption) {
        //         const userChoice = selectedOption.value;
        //         console.log("User selected:", userChoice);
        //         return userChoice;
        //       // You can now use userChoice variable anywhere!
        //     } else {
        //         console.log("No option selected");
        //         return null;
        //     }
        // }
        // let ok = saveChoice()

        function validateURL() {
            const textareaValue = document.getElementById('text_url').value.trim();
            const pattern = /^https?:\/\/.+\..+/;

            if (pattern.test(textareaValue)) {
                alert("Valid URL!");
            } else {
                alert("Please enter a valid URL starting with http:// or https://");
            }
        }

// loading button on click


document.addEventListener("DOMContentLoaded", function () {
    console.log("JS loaded ✅");
});



document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector('#tab1 form'); // Text form
    const button = document.getElementById("submit");
    const buttonText = document.getElementById("submit-text");
    const spinner = document.getElementById("spinner");

    form.addEventListener("submit", function () {
        // Activate loading
        button.disabled = true;
        spinner.classList.remove("d-none");
        buttonText.textContent = "Analyzing...";
    });
});

// handels the spinner after going back
document.addEventListener("DOMContentLoaded", function () {
    // Reset spinner and button state when user returns back via browser
    window.addEventListener("pageshow", function (event) {
        if (event.persisted || performance.getEntriesByType("navigation")[0].type === "back_forward") {
            const submitInput = document.getElementById("submit");
            const spinner = document.getElementById("spinner");

            if (submitInput) {
                submitInput.disabled = false;
                submitInput.textContent = "Analyze Sentiment"; // original value
            }

            if (spinner) {
                spinner.classList.add("d-none");
            }
        }
    });
});

// url button
document.addEventListener("DOMContentLoaded", function () {
    const formUrl = document.querySelector('#tab2 form');
    const submitBtnUrl = document.getElementById("submit-url");
    const submitTextUrl = document.getElementById("submit-url-text");
    const spinnerUrl = document.getElementById("spinner-url");

    if (formUrl && submitBtnUrl && spinnerUrl) {
        formUrl.addEventListener("submit", function () {
            submitBtnUrl.disabled = true;
            submitTextUrl.textContent = "Analyzing...";
            spinnerUrl.classList.remove("d-none");
        });
    }

    // Reset URL form state on back nav
    window.addEventListener("pageshow", function (event) {
        const isBack = event.persisted || performance.getEntriesByType("navigation")[0]?.type === "back_forward";
        if (isBack) {
            if (submitBtnUrl) {
                submitBtnUrl.disabled = false;
                submitTextUrl.textContent = "Analyze URL";
            }
            if (spinnerUrl) {
                spinnerUrl.classList.add("d-none");
            }
        }
    });
});





