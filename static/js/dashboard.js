document.addEventListener("DOMContentLoaded", () => {

    // Animate Statistics Cards
    const cards = document.querySelectorAll(".stat-card");

    cards.forEach((card, index) => {

        card.style.opacity = "0";
        card.style.transform = "translateY(30px)";

        setTimeout(() => {

            card.style.transition = "0.6s ease";
            card.style.opacity = "1";
            card.style.transform = "translateY(0)";

        }, index * 150);

    });

    // Sidebar Toggle
    const sidebar = document.querySelector(".sidebar");
    const mainContent = document.querySelector(".main-content");
    const toggleButton = document.getElementById("sidebarToggle");

    if (sidebar && mainContent && toggleButton) {

        toggleButton.addEventListener("click", () => {

            sidebar.classList.toggle("collapsed");
            mainContent.classList.toggle("expanded");

        });

    }

});