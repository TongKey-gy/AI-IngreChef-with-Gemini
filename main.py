<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>재료 기반 레시피 추천기</title>
    <!-- Tailwind CSS 로드 --><script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'primary-500': '#EF4444', // Red-500 for primary
                        'secondary-100': '#FEF3C7', // Amber-100 for background
                        'card-bg': '#FFF7ED', // Orange-50 for card background
                    },
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                }
            }
        }
    </script>
    <style>
        /* 사용자 지정 스크롤바 스타일 */
        #recipe-results::-webkit-scrollbar {
            width: 8px;
        }
        #recipe-results::-webkit-scrollbar-thumb {
            background-color: #FBBF24; /* Amber-400 */
            border-radius: 4px;
        }
        #recipe-results::-webkit-scrollbar-track {
            background-color: #FEF3C7; /* Secondary-100 */
        }
        .recipe-card {
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .recipe-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.2), 0 4px 6px -2px rgba(239, 68, 68, 0.1); /* Custom shadow with primary color */
        }
        
        /* 이전의 body와 overlay-container CSS 정의를 제거하고, 배경은 HTML 요소에 인라인 스타일로 직접 적용합니다. */
    </style>
</head>
<body class="min-h-screen font-sans">
    
    <!-- 
        배경 적용 방식 (흰색 오버레이 제거):
        1. 배경 이미지 URL을 직접 bg-url 인라인 스타일에 지정했습니다.
        2. 콘텐츠 가독성을 높이던 흰색 투명도(rgba(255, 255, 255, 0.9)) 오버레이를 제거하여 이미지가 선명하게 보이도록 했습니다.
        3. bg-cover, bg-fixed, bg-center 클래스를 사용하여 배경을 완벽하게 채웁니다.
    -->
    <div 
        class="min-h-screen bg-fixed bg-cover bg-center p-4 md:p-8" 
        style="background-image: url('https://images.unsplash.com/photo-1542838132-8415843a0d5c?fit=crop&w=1600&h=900&q=80');"
    >
        <div class="max-w-4xl mx-auto">
            <header class="text-center mb-8">
                <h1 class="text-4xl md:text-5xl font-extrabold text-primary-500 mb-2">🍽️ 냉장고 털기 레시피 추천</h1>
                <p class="text-gray-600 text-lg">가지고 있는 재료를 쉼표(,)로 구분하여 입력해 주세요. Gemini가 최고의 메뉴를 추천해 드립니다.</p>
            </header>

            <!-- 입력 섹션 --><div class="bg-white p-6 rounded-xl shadow-lg mb-8">
                <label for="ingredients" class="block text-lg font-semibold text-gray-700 mb-2">재료 입력 (예: 계란, 양파, 베이컨, 쌀)</label>
                <textarea id="ingredients" rows="3" class="w-full p-4 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500 resize-none text-gray-800" placeholder="사용 가능한 재료들을 입력하세요..."></textarea>
                
                <div id="message-box" class="mt-3 p-3 hidden rounded-lg text-sm" role="alert"></div>

                <button onclick="getRecipeRecommendations()" id="submit-btn" class="mt-4 w-full bg-primary-500 text-white font-bold py-3 rounded-lg hover:bg-red-600 transition duration-300 flex items-center justify-center">
                    <svg id="loading-spinner" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white hidden" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    레시피 추천받기
                </button>
            </div>

            <!-- 결과 섹션 --><h2 class="text-3xl font-bold text-gray-700 mb-4 border-b-2 border-primary-500 pb-2">추천 레시피 목록</h2>
            <div id="recipe-results" class="space-y-6 max-h-[80vh] overflow-y-auto">
                <p id="initial-message" class="text-center text-gray-500 p-8 bg-white rounded-xl shadow-inner">
                    재료를 입력하고 버튼을 눌러 추천을 시작하세요!
                </p>
            </div>
        </div>
    </div>

    <script>
        const API_KEY = ""; // 캔버스 환경에서 자동으로 제공됩니다.
        const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${API_KEY}`;
        
        const resultsContainer = document.getElementById('recipe-results');
        const ingredientsTextarea = document.getElementById('ingredients');
        const submitBtn = document.getElementById('submit-btn');
        const spinner = document.getElementById('loading-spinner');
        const initialMessage = document.getElementById('initial-message');
        const messageBox = document.getElementById('message-box');

        /**
         * 메시지 박스를 표시/숨김합니다.
         * @param {string} type 'success', 'error', 'info'
         * @param {string} message 표시할 메시지
         */
        function showMessage(type, message) {
            messageBox.textContent = message;
            messageBox.className = "mt-3 p-3 rounded-lg text-sm";
            messageBox.classList.remove('hidden');

            switch (type) {
                case 'error':
                    messageBox.classList.add('bg-red-100', 'text-red-700', 'border', 'border-red-400');
                    break;
                case 'info':
                    messageBox.classList.add('bg-blue-100', 'text-blue-700', 'border', 'border-blue-400');
                    break;
                case 'success':
                    messageBox.classList.add('bg-green-100', 'text-green-700', 'border', 'border-green-400');
                    break;
                default:
                    messageBox.classList.add('bg-gray-100', 'text-gray-700');
            }
        }
        
        function hideMessage() {
            messageBox.classList.add('hidden');
        }

        /**
         * 레시피 추천을 위한 Gemini API를 호출합니다.
         */
        async function getRecipeRecommendations() {
            hideMessage();
            const ingredients = ingredientsTextarea.value.trim();
            if (!ingredients) {
                showMessage('error', '재료를 입력해 주세요!');
                return;
            }

            // UI 상태 변경
            initialMessage.classList.add('hidden');
            resultsContainer.innerHTML = '';
            submitBtn.disabled = true;
            spinner.classList.remove('hidden');
            submitBtn.childNodes[1].nodeValue = ' 레시피 생성 중...';
            
            showMessage('info', '재료를 분석하여 레시피를 생성하고 있습니다. 잠시만 기다려 주세요...');


            const systemPrompt = `
                당신은 세계적인 요리사이자 AI 셰프입니다. 사용자가 제공한 재료만을 사용하여 만들 수 있는 독창적이고 맛있는 요리 메뉴 3가지를 한국어로 추천해야 합니다.
                각 레시피는 제목, 필요한 재료 목록(사용자 제공 재료 포함), 간단한 조리 방법(3~5단계), 그리고 레시피에 대한 팁이나 설명을 포함해야 합니다.
                반드시 다음 JSON 스키마에 따라 응답해야 하며, 다른 텍스트는 포함하지 마십시오.
            `;

            const userQuery = `내가 가진 재료는 다음과 같습니다: ${ingredients}. 이 재료들로 만들 수 있는 3가지 요리를 한국어로 추천하고 레시피를 구조화된 JSON 형식으로 제공해줘.`;

            const payload = {
                contents: [{ parts: [{ text: userQuery }] }],
                systemInstruction: { parts: [{ text: systemPrompt }] },
                generationConfig: {
                    responseMimeType: "application/json",
                    responseSchema: {
                        type: "ARRAY",
                        items: {
                            type: "OBJECT",
                            properties: {
                                "title": { "type": "STRING", "description": "추천 요리 이름 (예: 베이컨 계란 볶음밥)" },
                                "ingredients": {
                                    "type": "ARRAY",
                                    "items": { "type": "STRING" },
                                    "description": "요리에 필요한 재료 목록 (사용자가 입력한 재료 + 기타 필수 재료)"
                                },
                                "instructions": {
                                    "type": "ARRAY",
                                    "items": { "type": "STRING" },
                                    "description": "간단하고 명확한 조리 단계 (3~5단계)"
                                },
                                "chefTip": { "type": "STRING", "description": "레시피에 대한 팁이나 간단한 설명" }
                            },
                            "propertyOrdering": ["title", "ingredients", "instructions", "chefTip"]
                        }
                    }
                }
            };

            try {
                const response = await fetchWithExponentialBackoff(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(`API Error: ${result.error?.message || response.statusText}`);
                }
                
                const jsonText = result.candidates?.[0]?.content?.parts?.[0]?.text;
                if (!jsonText) {
                     throw new Error('API 응답에서 유효한 JSON 콘텐츠를 찾을 수 없습니다.');
                }
                
                const recommendedRecipes = JSON.parse(jsonText);

                renderRecipes(recommendedRecipes);
                showMessage('success', `${recommendedRecipes.length}개의 레시피 추천이 완료되었습니다!`);

            } catch (error) {
                console.error("Recipe Generation Error:", error);
                showMessage('error', `레시피 생성 중 오류가 발생했습니다: ${error.message}. 재료를 다시 확인해 주세요.`);
                initialMessage.classList.remove('hidden'); // 오류 시 초기 메시지 다시 표시

            } finally {
                // UI 상태 복구
                submitBtn.disabled = false;
                spinner.classList.add('hidden');
                submitBtn.childNodes[1].nodeValue = ' 레시피 추천받기';
            }
        }

        /**
         * Access Token 발급 요청을 위한 Exponential Backoff 로직
         */
        async function fetchWithExponentialBackoff(url, options, maxRetries = 5) {
            for (let i = 0; i < maxRetries; i++) {
                try {
                    const response = await fetch(url, options);
                    if (response.status !== 429) { // 429 Too Many Requests가 아니면 성공 또는 일반 오류
                        return response;
                    }
                    // 429 Too Many Requests일 경우 재시도 대기
                    console.log(`Rate limit exceeded. Retrying in ${2 ** i} seconds...`);
                } catch (error) {
                    console.log(`Fetch error. Retrying in ${2 ** i} seconds...`);
                }

                if (i < maxRetries - 1) {
                    await new Promise(resolve => setTimeout(resolve, (2 ** i) * 1000));
                }
            }
            // 최종 실패 처리
            return new Response(JSON.stringify({ error: { message: "API 요청이 최대 재시도 횟수를 초과하여 실패했습니다." } }), { status: 500, headers: { 'Content-Type': 'application/json' } });
        }


        /**
         * 추천받은 레시피 배열을 HTML로 렌더링합니다.
         * @param {Array<Object>} recipes 레시피 객체 배열
         */
        function renderRecipes(recipes) {
            resultsContainer.innerHTML = '';
            
            if (recipes.length === 0) {
                resultsContainer.innerHTML = '<p class="text-center text-gray-500 p-8">추천할 수 있는 레시피가 없습니다. 재료를 더 추가해 보세요!</p>';
                return;
            }

            recipes.forEach((recipe, index) => {
                const ingredientsHtml = recipe.ingredients.map(ing => 
                    `<li class="flex items-center text-sm text-gray-700">
                        <svg class="w-4 h-4 mr-2 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        ${ing}
                    </li>`
                ).join('');

                const instructionsHtml = recipe.instructions.map((step, stepIndex) => 
                    `<li class="mb-2 text-gray-800">
                        <span class="font-bold text-primary-500 mr-2">${stepIndex + 1}.</span> ${step}
                    </li>`
                ).join('');

                const cardHtml = `
                    <div class="recipe-card bg-card-bg p-6 rounded-xl shadow-md border-t-4 border-primary-500">
                        <h3 class="text-2xl font-bold text-gray-800 mb-3">${recipe.title}</h3>
                        
                        <!-- 재료 섹션 --><div class="mb-4 p-4 bg-white rounded-lg shadow-inner">
                            <h4 class="text-lg font-semibold text-primary-500 mb-2 border-b border-gray-200 pb-1">필요 재료</h4>
                            <ul class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                ${ingredientsHtml}
                            </ul>
                        </div>

                        <!-- 조리법 섹션 --><div class="mb-4">
                            <h4 class="text-lg font-semibold text-gray-800 mb-2 border-b border-gray-200 pb-1">조리 방법</h4>
                            <ol class="list-none pl-0">
                                ${instructionsHtml}
                            </ol>
                        </div>

                        <!-- 셰프 팁 --><div class="p-3 bg-red-50 rounded-lg border border-red-200 text-sm text-gray-700">
                            <span class="font-bold text-red-600">👨‍🍳 셰프의 팁:</span> ${recipe.chefTip}
                        </div>
                    </div>
                `;
                resultsContainer.innerHTML += cardHtml;
            });
        }
    </script>
</body>
</html>
