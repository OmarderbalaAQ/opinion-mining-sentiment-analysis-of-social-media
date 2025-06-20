const output_text = document.querySelector("#res");

if(output_text.innerHTML == "neutral"){
    output_text.style.color = "#6b7280";
}else if(output_text.innerHTML == "positive"){
    output_text.style.color = "green"
}else if(output_text.innerHTML == "negative"){
    output_text.style.color = "red"
}


// word counting
document.addEventListener("DOMContentLoaded", function () {
    const analyzedElement = document.querySelector(".analyzed-text");
    const wordCountDiv = document.getElementById("word-count");

    if (analyzedElement && wordCountDiv) {
        function countWords(text) {
            const words = text.trim().split(/\s+/);
            return words.filter(word => word.length > 0).length;
        }

        const content = analyzedElement.textContent || analyzedElement.innerText || "";
        const wordCount = countWords(content);
        wordCountDiv.textContent = wordCount;
    } else {
        console.warn("Could not find analyzed text or word count element.");
    }

});


