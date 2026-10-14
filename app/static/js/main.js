async function toggleFavorite(event, btn, variant_id, logged_in) {
    event.stopPropagation();

    try {
        if (!logged_in) {
            window.location.href = "/login";
            return;
        }

        const response = await fetch(`/api/favorites/${variant_id}`, {
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

async function navBarRouting(event, btn, logged_in, path) {
    event.stopPropagation();

    if (!logged_in) {
        window.location.href = "/login";
        return;
    }

    window.location.href = path;
}

async function addInvestment(event, btn, variant_id) {
    event.stopPropagation();

    try {
        const investment = sessionStorage.getItem("investmentConfiguration");
        const options = { method: "POST" };
        if (investment) {
            options.headers = { "Content-Type": "application/json" };
            options.body = investment;
        }

        const response = await fetch(`/api/my_investments/${variant_id}`, {
            ...options,
        });

        if (!response.ok) {
            throw new Error("Failed to add investment");
        }

        const data = await response.json();

    } catch (error) {
        console.error("Could not add investment:", error);
    }
}

const configurator = document.getElementById("investment-configurator");
if (configurator) {
    configurator.addEventListener("submit", showRecommendations);
}

const showMoreButton = document.getElementById("show-more-recommendations");
if (showMoreButton) {
    showMoreButton.addEventListener("click", () => {
        document.querySelectorAll("[data-product-card][data-recommendation-match]").forEach((card) => {
            card.hidden = false;
        });
        showMoreButton.hidden = true;
    });
}

function showRecommendations(event) {
    event.preventDefault();

    const amount = Number(document.getElementById("input-amount").value);
    const horizonMonths = Number(document.getElementById("input-horizon").value);
    const productTypes = [...document.querySelectorAll("[data-product-filter]:checked")].map(
        (input) => input.dataset.productFilter,
    );
    const payoutMethods = [...document.querySelectorAll("[data-payout-filter]:checked")].map(
        (input) => input.dataset.payoutFilter,
    );
    const configuration = {
        amount,
        horizon_months: horizonMonths,
        product_types: productTypes,
        payout_methods: payoutMethods,
    };
    sessionStorage.setItem("investmentConfiguration", JSON.stringify(configuration));

    const horizonDays = horizonMonths * 365.25 / 12;
    const cards = [...document.querySelectorAll("#recommendation-list [data-product-card]")];
    const matches = cards.filter((card) => {
        const minAmount = Number(card.dataset.minAmount);
        const maxAmount = Number(card.dataset.maxAmount);
        const termDays = Number(card.dataset.termDays);
        const isBankDeposit = card.dataset.productType !== "treasury_bond";
        const productTypeAllowed = isBankDeposit
            ? productTypes.includes("bank_deposits")
            : productTypes.includes("treasury_bonds");
        const capitalization = card.dataset.capitalization;
        const payoutAllowed = !capitalization
            || (payoutMethods.includes("at_end") && ["at_maturity", "at_promo_end"].includes(capitalization))
            || (payoutMethods.includes("during_term") && ["monthly", "quarterly", "daily", "annual"].includes(capitalization));

        return productTypeAllowed
            && payoutAllowed
            && (!minAmount || amount >= minAmount)
            && (!maxAmount || amount <= maxAmount)
            && (!termDays || termDays <= horizonDays);
    });

    matches.sort((first, second) => Number(second.dataset.rate || 0) - Number(first.dataset.rate || 0));
    cards.forEach((card) => {
        card.hidden = true;
        card.removeAttribute("data-recommendation-match");
    });
    matches.forEach((card, index) => {
        card.dataset.recommendationMatch = "true";
        card.hidden = index >= 5;
        document.getElementById("recommendation-list").appendChild(card);
    });

    document.getElementById("recommendations").hidden = false;
    document.getElementById("no-recommendations").hidden = matches.length > 0;
    showMoreButton.hidden = matches.length <= 5;
    document.getElementById("recommendations").scrollIntoView({ behavior: "smooth", block: "start" });
}

function toggleFilter(contentId, chevronId) {
    const content = document.getElementById(contentId);
    const chevron = document.getElementById(chevronId);

    if (!content) return;
    content.classList.toggle("expanded");
    chevron?.classList.toggle("rotate-180");
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
