/* Casino Bot - Mini App Game Logic */

// Global state
let userId = null;
let userCoins = 0;
let currentBet = 50;
let spinning = false;

// Initialize Telegram WebApp
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
}

// API helper
async function api(endpoint, data = {}) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { error: 'Network error' };
    }
}

// Initialize user
async function initUser() {
    const initData = tg?.initData || '';
    const userData = tg?.initDataUnsafe?.user || {};

    const result = await api('/api/user', {
        init_data: initData,
        username: userData.username,
        first_name: userData.first_name
    });

    if (result.error) {
        alert('Failed to load user data');
        return;
    }

    userId = result.id;
    userCoins = result.coins;

    document.getElementById('username').textContent = result.first_name || result.username || 'Player';
    document.getElementById('coins').textContent = userCoins.toLocaleString();
    document.getElementById('profile-username').textContent = result.username || '-';
    document.getElementById('profile-coins').textContent = userCoins.toLocaleString();
    document.getElementById('profile-items').textContent = result.items;
    document.getElementById('profile-refcode').textContent = result.referral_code;

    // Hide loading
    document.getElementById('loading').classList.add('hidden');
}

// Claim daily reward
async function claimDaily() {
    const result = await api('/api/daily', { user_id: userId });

    if (result.success) {
        userCoins = result.balance;
        document.getElementById('coins').textContent = userCoins.toLocaleString();
        document.getElementById('profile-coins').textContent = userCoins.toLocaleString();
        document.getElementById('daily-status').textContent = 'CLAIMED ✓';
        alert(`🎁 Claimed ${result.coins} coins!`);
    } else {
        alert(`⏰ Next daily in: ${result.next_claim}`);
    }
}

// Open case
async function openCase(caseId) {
    const result = await api('/api/case/open', {
        user_id: userId,
        case_id: caseId
    });

    if (result.success) {
        userCoins = result.balance;
        document.getElementById('coins').textContent = userCoins.toLocaleString();
        document.getElementById('profile-coins').textContent = userCoins.toLocaleString();

        // Show case opening modal
        const item = result.item;
        const icons = {
            common: '🪙', uncommon: '💍', rare: '💎', epic: '🔮', legendary: '👑'
        };

        document.getElementById('revealed-item').textContent = icons[item.rarity] || '🎁';
        document.getElementById('item-name').textContent = item.name;
        document.getElementById('item-rarity').textContent = item.rarity;
        document.getElementById('item-rarity').className = `rarity ${item.rarity}`;
        document.getElementById('item-value').textContent = `Value: ${item.value} coins`;

        document.getElementById('case-modal').classList.remove('hidden');
    } else {
        alert(result.message || 'Not enough coins!');
    }
}

// Close case modal
function closeCaseModal() {
    document.getElementById('case-modal').classList.add('hidden');
}

// Show roulette screen
function showRoulette() {
    showScreen('roulette');
}

// Set bet amount
function setBet(amount) {
    currentBet = amount;
    document.getElementById('current-bet').textContent = amount;
}

// Spin roulette
async function spinRoulette(color) {
    if (spinning) return;
    spinning = true;

    const wheel = document.getElementById('wheel');
    const resultBox = document.getElementById('roulette-result');

    // Animate wheel
    wheel.style.transform = `rotate(${Math.random() * 360 + 720}deg)`;
    resultBox.classList.add('hidden');

    const result = await api('/api/roulette/spin', {
        user_id: userId,
        bet: currentBet,
        color: color
    });

    setTimeout(() => {
        spinning = false;

        if (result.success) {
            userCoins = result.balance;
            document.getElementById('coins').textContent = userCoins.toLocaleString();
            document.getElementById('profile-coins').textContent = userCoins.toLocaleString();

            resultBox.classList.remove('hidden');
            if (result.won > 0) {
                resultBox.className = 'result-box win';
                resultBox.textContent = `🎉 You won ${result.won} coins! (${result.result})`;
            } else {
                resultBox.className = 'result-box lose';
                resultBox.textContent = `😔 You lost! (${result.result})`;
            }
        } else {
            alert(result.message || 'Not enough coins!');
        }
    }, 500);
}

// Show screen
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(`${screenId}-screen`).classList.add('active');

    if (screenId === 'inventory') loadInventory();
    if (screenId === 'menu') refreshBalance();
}

// Load inventory
async function loadInventory() {
    const result = await api('/api/inventory', { user_id: userId });
    const list = document.getElementById('inventory-list');

    if (result.items && result.items.length > 0) {
        list.innerHTML = result.items.map(item => `
            <div class="inv-item ${item.rarity}">
                <div class="item-icon">${getRarityIcon(item.rarity)}</div>
                <h4>${item.name}</h4>
                <p class="item-value">${item.value} coins</p>
            </div>
        `).join('');
    } else {
        list.innerHTML = '<p style="text-align:center;color:#888;">No items yet. Open some cases!</p>';
    }
}

// Get rarity icon
function getRarityIcon(rarity) {
    const icons = {
        common: '🪙', uncommon: '💍', rare: '💎', epic: '🔮', legendary: '👑'
    };
    return icons[rarity] || '🎁';
}

// Refresh balance
async function refreshBalance() {
    const result = await api('/api/stats', { user_id: userId });
    if (result.coins !== undefined) {
        userCoins = result.coins;
        document.getElementById('coins').textContent = userCoins.toLocaleString();
        document.getElementById('profile-coins').textContent = userCoins.toLocaleString();
    }
}

// Share referral
function shareReferral() {
    const refCode = document.getElementById('profile-refcode').textContent;
    const link = `https://t.me/${tg?.initDataUnsafe?.user ? 'your_bot_username' : 'bot'}?start=ref_${refCode}`;

    if (tg?.shareMessage) {
        tg.shareMessage(link);
    } else if (navigator.share) {
        navigator.share({ title: 'Join Casino Bot!', url: link });
    } else {
        navigator.clipboard.writeText(link);
        alert('Referral link copied!');
    }
}

// Init on load
document.addEventListener('DOMContentLoaded', initUser);
