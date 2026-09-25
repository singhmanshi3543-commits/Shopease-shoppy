const words = [
    "Frontend Developer",
    "Python Developer",
    "Problem Solver",
    "CSE Student"
];

let i = 0;
let j = 0;
let currentWord = "";
let isDeleting = false;

function type() {

    currentWord = words[i];

    if (isDeleting) {
        document.getElementById("typing").textContent =
            currentWord.substring(0, j--);
    } else {
        document.getElementById("typing").textContent =
            currentWord.substring(0, j++);
    }

    if (!isDeleting && j === currentWord.length + 1) {

        isDeleting = true;

        setTimeout(type, 1000);

        return;

    }

    if (isDeleting && j === 0) {

        isDeleting = false;

        i++;

        if (i === words.length)
            i = 0;

    }

    setTimeout(type, isDeleting ? 60 : 120);

}

type();
// Scroll Reveal Animation

const hiddenElements = document.querySelectorAll(".hidden");

const observer = new IntersectionObserver((entries) => {

    entries.forEach((entry) => {

        if(entry.isIntersecting){

            entry.target.classList.add("show");

        }

    });

});

hiddenElements.forEach((el)=>observer.observe(el));
// Dark Mode

const themeBtn = document.getElementById("theme-btn");

themeBtn.addEventListener("click",()=>{

    document.body.classList.toggle("dark");

    if(document.body.classList.contains("dark")){

        themeBtn.innerHTML="☀️";

    }

    else{

        themeBtn.innerHTML="🌙";

    }

});
// Back To Top Button

const topBtn = document.getElementById("topBtn");

window.onscroll = function(){

    if(document.documentElement.scrollTop > 300){

        topBtn.style.display = "block";

    }else{

        topBtn.style.display = "none";

    }

};

topBtn.onclick = function(){

    window.scrollTo({

        top:0,

        behavior:"smooth"

    });

};
// EmailJS Initialize
emailjs.init({
    publicKey: "hhZf_A01MlgTRgJ3F"
});

// Contact Form
const form = document.querySelector(".contact-form");

form.addEventListener("submit", function(e) {
    e.preventDefault();

    emailjs.sendForm(
        "service_u56tuga",
        "template_lvldmft",
        this
    )
    .then(function() {
        alert("Message sent successfully! Thank you 😊");
        form.reset();
    })
    .catch(function(error) {
        console.log(error);
        alert("Failed to send message. Please try again.");
        
    });
});
// Hamburger Menu

const hamburger = document.querySelector(".hamburger");

const navLinks = document.querySelector(".nav-links");

hamburger.addEventListener("click", () => {

    navLinks.classList.toggle("active");

});