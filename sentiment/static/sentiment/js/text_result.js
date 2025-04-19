console.log("hello from result")
const output_text = document.getElementById('sent')

if(output_text.innerHTML == "neutral"){
    output_text.style.color = "yellow";
}else if(output_text.innerHTML == "positive"){
    output_text.style.color = "green"
}else if(output_text.innerHTML == "negative"){
    output_text.style.color = "red"
}
console.log(output_text.value);
