// DataScope AI — Jenkins Pipeline
// Stages: Build, Test, Code Quality, Security (Deploy/Release/Monitor added incrementally)

pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '15'))
        disableConcurrentBuilds()
    }

    environment {
        BACKEND_SLIM_TAG = "slim-${env.BUILD_NUMBER}"
        BACKEND_FULL_TAG = "full-${env.BUILD_NUMBER}"
        FRONTEND_TAG     = "fe-${env.BUILD_NUMBER}"
        MOCK_TAG         = "mock-${env.BUILD_NUMBER}"
        REGISTRY_PREFIX  = "datascope"

        // Shared Trivy cache across stages (the DB is large, only download once)
        TRIVY_CACHE_DIR  = "/tmp/trivy-cache"
    }

    stages {
        stage('Checkout') {
            steps {
                sh '''
                    echo "===> Working directory: $(pwd)"
                    echo "===> Commit: $(git log -1 --oneline)"
                    echo "===> Files in root:"
                    ls -la
                '''
            }
        }

        stage('Build') {
            parallel {
                stage('Backend (slim)') {
                    steps {
                        sh '''
                            echo "===> Building ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG}"
                            docker build \
                                -f backend/Dockerfile.slim \
                                -t ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG} \
                                backend/
                            docker images ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG} --format "{{.Size}}"
                        '''
                    }
                }
                stage('Frontend') {
                    steps {
                        sh '''
                            echo "===> Building ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG}"
                            docker build \
                                -f frontend/Dockerfile \
                                -t ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG} \
                                --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 \
                                frontend/
                            docker images ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG} --format "{{.Size}}"
                        '''
                    }
                }
                stage('Ollama Mock') {
                    steps {
                        sh '''
                            echo "===> Building ${REGISTRY_PREFIX}-ollama-mock:${MOCK_TAG}"
                            docker build \
                                -f backend/mock-ollama/Dockerfile \
                                -t ${REGISTRY_PREFIX}-ollama-mock:${MOCK_TAG} \
                                backend/mock-ollama/
                            docker images ${REGISTRY_PREFIX}-ollama-mock:${MOCK_TAG} --format "{{.Size}}"
                        '''
                    }
                }
            }
        }

        stage('Test (Backend Unit)') {
            steps {
                sh '''
                    echo "===> Setting up Python venv for tests"
                    cd backend
                    python3 -m venv .venv-ci
                    . .venv-ci/bin/activate

                    echo "===> Installing dev dependencies"
                    pip install --quiet --upgrade pip
                    pip install --quiet -r requirements-dev.txt

                    echo "===> Running pytest"
                    pytest -v \
                        --junitxml=test-results.xml \
                        --cov=app \
                        --cov-report=xml:coverage.xml \
                        --cov-report=term
                '''
            }
            post {
                always {
                    junit testResults: 'backend/test-results.xml', allowEmptyResults: false
                    archiveArtifacts artifacts: 'backend/coverage.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Code Quality (SonarCloud)') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'

                    withCredentials([string(credentialsId: 'sonarcloud-token', variable: 'SONAR_TOKEN')]) {
                        sh """
                            echo '===> Running SonarCloud analysis'
                            ${scannerHome}/bin/sonar-scanner \\
                                -Dsonar.host.url=https://sonarcloud.io \\
                                -Dsonar.token=\$SONAR_TOKEN \\
                                -Dsonar.projectKey=Exile404_Datascope-AI \\
                                -Dsonar.organization=exile404
                        """
                    }
                }
            }
        }

        stage('Security') {
            // Sub-stages run sequentially. Trivy uses a shared BoltDB cache
            // that doesn't handle concurrent writers, so parallelising the
            // two trivy scans caused DB corruption in build #5. npm audit
            // also serialised here for predictable log order.
            stages {
                stage('Trivy: prime DB') {
                    steps {
                        sh '''
                            echo "===> Priming Trivy vulnerability DB (shared by all scans)"
                            mkdir -p ${TRIVY_CACHE_DIR}
                            trivy image --download-db-only --cache-dir ${TRIVY_CACHE_DIR}
                            echo "===> Cache contents:"
                            ls -la ${TRIVY_CACHE_DIR}
                        '''
                    }
                }
                stage('Trivy: backend slim') {
                    steps {
                        sh '''
                            echo "===> Trivy scanning ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG}"
                            mkdir -p security-reports

                            trivy image \
                                --cache-dir ${TRIVY_CACHE_DIR} \
                                --skip-db-update \
                                --severity HIGH,CRITICAL \
                                --ignorefile .trivyignore \
                                --no-progress \
                                --format table \
                                --output security-reports/trivy-backend-slim.txt \
                                ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG} || true

                            trivy image \
                                --cache-dir ${TRIVY_CACHE_DIR} \
                                --skip-db-update \
                                --severity HIGH,CRITICAL \
                                --ignorefile .trivyignore \
                                --no-progress \
                                --format json \
                                --output security-reports/trivy-backend-slim.json \
                                ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG} || true

                            echo "===> Trivy results (HIGH+CRITICAL) for backend slim:"
                            cat security-reports/trivy-backend-slim.txt || echo "(no report file generated)"

                            # Enforce: fail build on HIGH or CRITICAL
                            trivy image \
                                --cache-dir ${TRIVY_CACHE_DIR} \
                                --skip-db-update \
                                --severity HIGH,CRITICAL \
                                --ignorefile .trivyignore \
                                --no-progress \
                                --exit-code 1 \
                                ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG}
                        '''
                    }
                }
                stage('Trivy: frontend') {
                    steps {
                        sh '''
                            echo "===> Trivy scanning ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG}"
                            mkdir -p security-reports

                            trivy image \
                                --cache-dir ${TRIVY_CACHE_DIR} \
                                --skip-db-update \
                                --severity HIGH,CRITICAL \
                                --ignorefile .trivyignore \
                                --no-progress \
                                --format table \
                                --output security-reports/trivy-frontend.txt \
                                ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG} || true

                            trivy image \
                                --cache-dir ${TRIVY_CACHE_DIR} \
                                --skip-db-update \
                                --severity HIGH,CRITICAL \
                                --ignorefile .trivyignore \
                                --no-progress \
                                --format json \
                                --output security-reports/trivy-frontend.json \
                                ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG} || true

                            echo "===> Trivy results (HIGH+CRITICAL) for frontend:"
                            cat security-reports/trivy-frontend.txt || echo "(no report file generated)"

                            trivy image \
                                --cache-dir ${TRIVY_CACHE_DIR} \
                                --skip-db-update \
                                --severity HIGH,CRITICAL \
                                --ignorefile .trivyignore \
                                --no-progress \
                                --exit-code 1 \
                                ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG}
                        '''
                    }
                }
                stage('pnpm audit (frontend)') {
                    steps {
                        sh '''
                            echo "===> Installing frontend deps for audit"
                            mkdir -p security-reports
                            cd frontend
                            pnpm install --frozen-lockfile --prefer-offline

                            echo "===> Running pnpm audit"
                            # First run: capture machine-readable output, never fails
                            pnpm audit --audit-level=high --json \
                                > ../security-reports/pnpm-audit.json 2>&1 || true

                            # Second run: capture human-readable output, never fails
                            pnpm audit --audit-level=high \
                                > ../security-reports/pnpm-audit.txt 2>&1 || true

                            echo "===> pnpm audit output:"
                            cat ../security-reports/pnpm-audit.txt

                            # Third run: enforce. This one fails the build on high/critical.
                            pnpm audit --audit-level=high
                        '''
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'security-reports/**',
                                     allowEmptyArchive: true,
                                     fingerprint: true
                }
            }
        }
        stage('Deploy (staging)') {
            stages {
                stage('Stage: Up + Wait Healthy') {
                    steps {
                        sh '''
                            echo "===> Bringing up staging stack with images tagged for this build"

                            # Tear down any leftover staging stack from previous builds.
                            # Force volume removal so the metrics.db doesn't carry permission state.
                            docker compose -f docker-compose.staging.yml down -v --remove-orphans 2>/dev/null || true

                            # Boot the stack. BACKEND_TAG/FRONTEND_TAG/MOCK_TAG come from
                            # the top-level environment block, so compose uses *this* build's images.
                            export BACKEND_TAG=${BACKEND_SLIM_TAG}
                            export FRONTEND_TAG=${FRONTEND_TAG}
                            export MOCK_TAG=${MOCK_TAG}

                            docker compose -f docker-compose.staging.yml up -d

                            echo ""
                            echo "===> Waiting for services to report healthy (max 90s)"

                            # Poll docker compose ps until all services show (healthy),
                            # or 18 attempts (90 seconds) have elapsed.
                            for i in $(seq 1 18); do
                                STATUS=$(docker compose -f docker-compose.staging.yml ps --format "{{.Name}}|{{.Health}}")
                                echo "Attempt $i:"
                                echo "$STATUS"

                                BAD=$(echo "$STATUS" | grep -E "unhealthy|starting|Exited|Restarting" || true)
                                if [ -z "$BAD" ]; then
                                    echo ""
                                    echo "===> All services healthy"
                                    break
                                fi

                                if [ $i -eq 18 ]; then
                                    echo ""
                                    echo "===> TIMEOUT: not all services healthy after 90s"
                                    docker compose -f docker-compose.staging.yml logs --tail=50
                                    exit 1
                                fi

                                sleep 5
                            done

                            echo ""
                            echo "===> Final stack status:"
                            docker compose -f docker-compose.staging.yml ps
                        '''
                    }
                }
                stage('Smoke Tests') {
                    steps {
                        sh '''
                            echo "===> Smoke test 1/3: backend /health"
                            HEALTH=$(curl -sf http://localhost:8001/health)
                            echo "Response: $HEALTH"
                            echo "$HEALTH" | grep -q '"api":"ok"' || {
                                echo "FAIL: /health did not report api:ok"
                                exit 1
                            }
                            echo "$HEALTH" | grep -q '"llm":"ok"' || {
                                echo "FAIL: /health did not report llm:ok"
                                exit 1
                            }
                            echo "PASS: backend health OK"
                            echo ""

                            echo "===> Smoke test 2/3: backend happy path (POST /api/cost/calculate)"
                            RESPONSE=$(curl -sf -X POST http://localhost:8001/api/cost/calculate \\
                                -H "Content-Type: application/json" \\
                                -d '{"model":"gpt-4o","input_tokens":1000000,"output_tokens":500000}')
                            echo "Response: $RESPONSE"

                            # Assert: total_cost == 7.5
                            echo "$RESPONSE" | grep -q '"total_cost":7.5' || {
                                echo "FAIL: total_cost was not 7.5"
                                echo "Expected: gpt-4o @ 1M input ($2.50) + 500k output ($5.00) = $7.50"
                                exit 1
                            }
                            echo "PASS: cost calculation returned expected value"
                            echo ""

                            echo "===> Smoke test 3/3: frontend homepage (GET /)"
                            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/)
                            echo "HTTP code: $HTTP_CODE"
                            [ "$HTTP_CODE" = "200" ] || {
                                echo "FAIL: frontend did not return 200 (got $HTTP_CODE)"
                                exit 1
                            }
                            echo "PASS: frontend homepage OK"
                            echo ""

                            echo "===> All 3 smoke tests passed"
                        '''
                    }
                }
            }
            post {
                failure {
                    sh '''
                        echo "===> Deploy stage failed, tearing down staging stack"
                        docker compose -f docker-compose.staging.yml logs --tail=100 || true
                        docker compose -f docker-compose.staging.yml down -v --remove-orphans || true
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "===> Pipeline succeeded for build #${env.BUILD_NUMBER}"
        }
        failure {
            echo "===> Pipeline failed for build #${env.BUILD_NUMBER}"
        }
        always {
            sh '''
                docker rmi ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG} || true
                docker rmi ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG} || true
                docker rmi ${REGISTRY_PREFIX}-ollama-mock:${MOCK_TAG} || true
            '''
        }
    }
}
