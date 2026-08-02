// ==UserScript==
// @name         AI Creator Studio - 收集箱
// @namespace    http://aicreator.studio/
// @version      0.1
// @description  一键收集 B站/抖音/小红书视频链接到 AI Creator Studio 收集箱
// @author       AI Creator Studio
// @match        https://www.bilibili.com/video/*
// @match        https://www.douyin.com/video/*
// @match        https://www.xiaohongshu.com/explore/*
// @match        https://www.xiaohongshu.com/discovery/item/*
// @icon         https://raw.githubusercontent.com/your-icon.svg
// @grant        GM_addStyle
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_notification
// ==/UserScript==

(function() {
    'use strict';

    const STORAGE_KEY = 'aiStudioCollect';
    const PLATFORMS = {
        'www.bilibili.com': { name: 'B站', emoji: '📺', id: 'bilibili' },
        'www.douyin.com':   { name: '抖音', emoji: '🎵', id: 'douyin' },
        'www.xiaohongshu.com': { name: '小红书', emoji: '📕', id: 'xiaohongshu' }
    };

    function getPlatform() {
        const host = window.location.hostname;
        return PLATFORMS[host] || null;
    }

    function getVideoTitle() {
        // B站
        let title = document.querySelector('h1.video-title') ||
                    document.querySelector('h1.video-info-title') ||
                    document.querySelector('.video-title') ||
                    document.querySelector('title');
        // 抖音
        if (!title) title = document.querySelector('.video-info-title');
        if (!title) title = document.querySelector('title');
        return title ? title.textContent.trim().replace(/[_\-|].*$/, '').trim() : '未命名视频';
    }

    function getVideoUrl() {
        return window.location.href.split('?')[0].split('#')[0];
    }

    function collectVideo() {
        const platform = getPlatform();
        if (!platform) return;

        const item = {
            id: Date.now(),
            url: getVideoUrl(),
            title: getVideoTitle(),
            platform: platform.id,
            addedAt: new Date().toISOString(),
            status: 'pending'
        };

        // 保存到 localStorage
        try {
            let existing = [];
            const saved = localStorage.getItem('aiStudioInbox');
            if (saved) existing = JSON.parse(saved);
            // 去重
            const isDuplicate = existing.some(e => e.url === item.url);
            if (isDuplicate) {
                showToast('⏳ 已收集过了');
                return;
            }
            existing.unshift(item);
            localStorage.setItem('aiStudioInbox', JSON.stringify(existing));
            showToast(`✅ 已收集到 ${platform.name}\n${item.title.slice(0, 30)}...`);

            // 触发同一浏览器其他标签页的更新
            try {
                localStorage.setItem('aiStudioCollect', Date.now());
                localStorage.removeItem('aiStudioCollect');
            } catch(e) {}

            // 通知
            if (typeof GM_notification !== 'undefined') {
                GM_notification({
                    title: '📥 AI Creator Studio',
                    text: `已收集 ${platform.name} 视频：${item.title.slice(0, 20)}`,
                    timeout: 3000
                });
            }
        } catch(e) {
            showToast('❌ 收集失败：' + e.message);
        }
    }

    // 添加收集按钮
    function addCollectButton() {
        const platform = getPlatform();
        if (!platform) return;

        // 避免重复添加
        if (document.getElementById('ai-studio-collect-btn')) return;

        const btn = document.createElement('div');
        btn.id = 'ai-studio-collect-btn';
        btn.innerHTML = '📥 收集';
        btn.style.cssText = `
            display:inline-flex;align-items:center;gap:4px;padding:6px 14px;
            background:#8b5e3c;color:#fff;border-radius:20px;cursor:pointer;
            font-size:13px;font-weight:500;font-family:-apple-system,sans-serif;
            box-shadow:0 2px 8px rgba(139,94,60,0.3);transition:all 0.2s;
            user-select:none;border:none;position:relative;z-index:9999;
        `;
        btn.onmouseenter = () => { btn.style.transform = 'scale(1.05)'; btn.style.boxShadow = '0 4px 12px rgba(139,94,60,0.4)'; };
        btn.onmouseleave = () => { btn.style.transform = 'scale(1)'; btn.style.boxShadow = '0 2px 8px rgba(139,94,60,0.3)'; };
        btn.onclick = collectVideo;

        // 插入到页面
        const insertTargets = [
            // B站 - 视频标题下方
            '.video-title',
            '.video-info-title',
            // B站 - 视频信息区
            '.video-info-meta',
            // 抖音 - 视频信息区
            '.video-info-wrap',
            // 通用 - 视频操作区
            '.video-toolbar',
            '.opr-area',
            // 小红书 - 笔记操作区
            '.note-scroller',
            '.interaction-container',
            '.title-container'
        ];

        let inserted = false;
        for (const sel of insertTargets) {
            const el = document.querySelector(sel);
            if (el && el.parentNode) {
                el.parentNode.insertBefore(btn, el.nextSibling);
                inserted = true;
                break;
            }
        }

        // 如果没找到插入点，加到页面右上角
        if (!inserted) {
            btn.style.position = 'fixed';
            btn.style.top = '80px';
            btn.style.right = '20px';
            btn.style.zIndex = '9999';
            document.body.appendChild(btn);
        }
    }

    // 简易 Toast 提示
    function showToast(msg) {
        const toast = document.createElement('div');
        toast.textContent = msg;
        toast.style.cssText = `
            position:fixed;bottom:80px;left:50%;transform:translateX(-50%);
            background:#2c241b;color:#fff;padding:10px 20px;border-radius:12px;
            font-size:13px;font-family:-apple-system,sans-serif;
            box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:99999;
            white-space:pre-line;text-align:center;max-width:80%;
            animation:fadeInUp 0.3s ease;
        `;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.transition = 'opacity 0.3s';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 2500);
    }

    // 添加全局动画
    GM_addStyle(`
        @keyframes fadeInUp {
            from { opacity:0; transform:translateX(-50%) translateY(10px); }
            to { opacity:1; transform:translateX(-50%) translateY(0); }
        }
    `);

    // 页面加载完成后尝试添加按钮
    function tryAdd() {
        if (document.querySelector('h1, .video-title, .video-info-title')) {
            addCollectButton();
        } else {
            setTimeout(tryAdd, 1000);
        }
    }

    // 初始执行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', tryAdd);
    } else {
        tryAdd();
    }

    // 监听页面变化（SPA 路由）
    let lastUrl = location.href;
    new MutationObserver(() => {
        const url = location.href;
        if (url !== lastUrl) {
            lastUrl = url;
            setTimeout(tryAdd, 1500);
        }
    }).observe(document, { subtree: true, childList: true });

})();