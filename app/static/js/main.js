async function toggleFavorite(event, btn, productId) {
    event.stopPropagation();

    try {
        const response = await fetch(`/api/favorites/${productId}`, {
            method: "POST",
        });

        if (!response.ok) {
            throw new Error("Failed to update favorite");
        }

        const data = await response.json();

        const heartIcon = btn.querySelector(".material-symbols-outlined");

        heartIcon.classList.toggle("filled", data.is_favorite);

        const actionText = data.is_favorite
            ? "Remove from favorites"
            : "Add to favorites";

        btn.setAttribute("title", actionText);
        btn.setAttribute("aria-label", actionText);

    } catch (error) {
        console.error("Could not update favorite:", error);
    }
}

function toggleFilter(contentId, chevronId) {
    const content = document.getElementById(contentId);
    const chevron = document.getElementById(chevronId);

    content.classList.toggle("expanded");
    chevron.classList.toggle("rotate-180");
}

function togglePasswordVisibility() {
    const pwdInput = document.getElementById("signin-password");
    const eyeIcon = document.getElementById("pwdEyeIcon");
    if (!pwdInput || !eyeIcon) return;

    if (pwdInput.type === "password") {
        pwdInput.type = "text";
        eyeIcon.textContent = "visibility_off";
    } else {
        pwdInput.type = "password";
        eyeIcon.textContent = "visibility";
    }
}

function toggleConfirmPasswordVisibility() {
    const confirmInput = document.getElementById("confirm-password");
    const eyeIcon = document.getElementById("confirmPwdEyeIcon");
    if (!confirmInput || !eyeIcon) return;

    if (confirmInput.type === "password") {
        confirmInput.type = "text";
        eyeIcon.textContent = "visibility_off";
    } else {
        confirmInput.type = "password";
        eyeIcon.textContent = "visibility";
    }
}

document.getElementById("signupForm")?.addEventListener("submit", signup);

async function signup(event) {
    event.preventDefault();

    const fullName = document.getElementById("signin-fullname").value;
    const email = document.getElementById("signin-email").value;
    const password = document.getElementById("signin-password").value;
    const repeatPassword = document.getElementById("confirm-password").value;

    if (password !== repeatPassword) {
        console.error("Passwords do not match");
        return;
    }

    console.log("Full name:", fullName);
    console.log("Email:", email);
    console.log("Password:", password);

    const response = await fetch("/api/users", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            full_name: fullName,
            email: email,
            password: password
        })
    });

    if (!response.ok) {
        console.error("Failed to create account");
        return;
    }

    const data = await response.json();

    console.log("Server response:", data);
}

async function login(event) {
    event.preventDefault();

    const email = document.getElementById("signin-email").value;
    const password = document.getElementById("signin-password").value;

    const response = await fetch("/api/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email: email,
            password: password
        })
    });

    if (!response.ok) {
        console.error("Login failed");
        return;
    }

    const data = await response.json();

    console.log("Login successful:", data);

    window.location.href = "/";
}

const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", login);
}
