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

        let savedChoice;

        document.querySelectorAll('input[name="option"]').forEach(option => {
            option.addEventListener('change', function() {
                savedChoice = this.value;
                console.log("Saved choice is:", savedChoice);
            });
        });

        const numberSelect = document.getElementById('numberSelect');
        function populateDropdownWithDOM() {
            // Clear any existing options
            numberSelect.innerHTML = '';
            
            // Create a document fragment to improve performance
            const fragment = document.createDocumentFragment();
            
            // Create and append each option
            for (let i = 1; i <= 100; i++) {
                const option = document.createElement('option');
                option.value = i.toString();
                option.textContent = i.toString();
                
                // You can add custom attributes or conditional styling here
                if (i % 10 === 0) {
                    option.classList.add('decade');
                    option.style.fontWeight = 'bold';
                }
                
                // Add the option to the fragment
                fragment.appendChild(option);
            }
            
            // Append all options to the select element at once
            numberSelect.appendChild(fragment);
        }
        
        // Call the function to populate the dropdown
        populateDropdownWithDOM();
        const selectedValue = 1
        numberSelect.addEventListener('change', function() {
            const selectedValue = this.value;
            console.log("number of images is",selectedValue)
        })

        function validateURL() {
            const textareaValue = document.getElementById('text_url').value.trim();
            const pattern = /^https?:\/\/.+\..+/;

            if (pattern.test(textareaValue)) {
                alert("Valid URL!");
            } else {
                alert("Please enter a valid URL starting with http:// or https://");
            }
        }