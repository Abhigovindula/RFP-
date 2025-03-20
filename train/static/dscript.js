document.getElementById("chatButton").addEventListener("click", function() {
    document.getElementById("chatSidebar").style.display = "flex";
});

document.getElementById("closeChat").addEventListener("click", function() {
    document.getElementById("chatSidebar").style.display = "none";
});

function sendMessage() {
    let userMessage = document.getElementById("userInput").value;
    let chatbox = document.getElementById("chatbox");

    // Display user message
    chatbox.innerHTML += `<p><b>You:</b> ${userMessage}</p>`;

    fetch(`/chatbot?message=${userMessage}`)
        .then(response => response.json())
        .then(data => {
            chatbox.innerHTML += `<p><b>Bot:</b> ${data.reply}</p>`;
            chatbox.scrollTop = chatbox.scrollHeight;
        });

    document.getElementById("userInput").value = "";
}
