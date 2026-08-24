/* Casino Bot - Game Logic (works in Telegram + browser) */

let userId = null;
let userCoins = 0;
let currentBet = 50;
let spinning = false;

// Get Telegram WebApp context
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
try {
    // Try to get user from Telegram
    let userData = null;
    if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
        userData = tg.initDataUnsafe.user;
        userId = userData.id;
    } else {
        // Browser test mode - use test user
        userId = 123456789;
        userData = { id: userId, username: "test_user", first_name: "Test Player" };
        console.log("Running in browser test mode");
    }

    // Load user from API
    const result = await api('/api/user', { user_id: userId });

    if (result.error) {
        document.getElementById('loading').innerHTML = '<p>Error loading user data</p>';
        return;
    }

    userCoins = result.coins || 0;

    // Update UI
    document.getElementById('username').textContent = result.first_name || result.username || 'Player';
    document.getElementById('coins').textContent = userCoins.toLocaleString();
    document.getElementById('profile-username').textContent = result.username || '-';
    document.getElementById('profile-coins').textContent = userCoins.toLocaleString();
    document.getElementById('profile-items').textContent = result.items || 0;
    document.getElementById('profile-refcode').textContent = result.referral_code || '-';

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
        alert(`🎁 Claimed ${result.coins} coins! Streak: ${result.streak} days`);
    } else {
        alert(`⏰ Next daily in: ${result.next_claim}`);
    }
}

// Open case
async function openCase(caseId) {
    const result = await api('/api/case/open', { user_id: userId, case_id: caseId });

    if (result.success) {
        userCoins = result.balance;
        document.getElementById('coins').textContent = userCoins.toLocaleString();
        document.getElementById('profile-coins').textContent = userCoins.toLocaleString();

        const item = result.item;
        document.getElementById('revealed-item').textContent = item.emoji || '🎁';
        document.getElementById('item-name').textContent = item.name;
        document.getElementById('item-rarity').textContent = item.rarity;
        document.getElementById('item-rarity').className = `rarity ${item.rarity}`;
        document.getElementById('item-value').textContent = `Value: ${item.value} coins`;

        document.getElementById('case-modal').classList.remove('hidden');
    } else {
        alert(result.message || 'Not enough coins!');
    }
}

function closeCaseModal() {
    document.getElementById('case-modal').classList.add('hidden');
}

function showRoulette() {
    showScreen('roulette');
}

function setBet(amount) {
    currentBet = amount;
    document.getElementById('current-bet').textContent = amount;
}

async function spinRoulette(color) {
    if (spinning) return;
    spinning = true;

    const wheel = document.getElementById('wheel');
    const resultBox = document.getElementById('roulette-result');

    wheel.style.transform = `rotate(${Math.random() * 360 + 720}deg)`;
    resultBox.classList.add('hidden');

    const result = await api('/api/roulette/spin', { user_id: userId, bet: currentBet, color: color });

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

// Slots
let slotSpinning = false;

async function spinSlots() {
    if (slotSpinning) return;
    slotSpinning = true;

    const bet = currentBet;
    const result = await api('/api/slots/spin', { user_id: userId, bet: bet });

    if (result.success) {
        userCoins = result.balance;
        document.getElementById('coins').textContent = userCoins.toLocaleString();

        // Animate slots
        const slots = ['slot1', 'slot2', 'slot3'];
        slots.forEach((id, i) => {
            document.getElementById(id).textContent = result.symbols[i];
        });

        const resultBox = document.getElementById('slots-result');
        resultBox.classList.remove('hidden');

        if (result.won > 0) {
            resultBox.className = 'result-box win';
            resultBox.textContent = `🎉 You won ${result.won} coins! (${result.symbols.join(' ')})`;
        } else {
            resultBox.className = 'result-box lose';
            resultBox.textContent = `😔 You lost! (${result.symbols.join(' ')})`;
        }
    } else {
        alert(result.message || 'Not enough coins!');
    }

    slotSpinning = false;
}

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(`${screenId}-screen`).classList.add('active');

    if (screenId === 'inventory') loadInventory();
    if (screenId === 'menu') refreshBalance();
}

async function loadInventory() {
    const result = await api('/api/inventory', { user_id: userId });
    const list = document.getElementById('inventory-list');

    if (result.items && result.items.length > 0) {
        list.innerHTML = result.items.map(item => `
            <div class="inv-item ${item.rarity}">
                <div class="item-icon">${item.emoji || '🎁'}</div>
                <h4>${item.name}</h4>
                <p class="item-value">${item.value} coins</p>
            </div>
        `).join('');
    } else {
        list.innerHTML = '<p style="text-align:center;color:#888;">No items yet. Open some cases!</p>';
    }
}

async function refreshBalance() {
    const result = await api('/api/stats', { user_id: userId });
    if (result.coins !== undefined) {
        userCoins = result.coins;
        document.getElementById('coins').textContent = userCoins.toLocaleString();
        document.getElementById('profile-coins').textContent = userCoins.toLocaleString();
    }
}

function shareReferral() {
    const refCode = document.getElementById('profile-refcode').textContent;
    const link = `https://t.me/${tg?.initDataUnsafe?.user ? 'MyCasinoBotx_bot' : 'MyCasinoBotx_bot'}?start=ref_${refCode}`;

    if (navigator.share) {
        navigator.share({ title: 'Join Casino Bot!', url: link });
    } else {
        navigator.clipboard.writeText(link);
        alert('Referral link copied!');
    }
}

document.addEventListener('DOMContentLoaded', () => initUser().catch(e => { console.error(e); document.getElementById('loading').classList.add('hidden'); }));
