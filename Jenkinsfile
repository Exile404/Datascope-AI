// DataScope AI — Jenkins Pipeline
// Stages: Build, Test, Code Quality, Security (Deploy/Release/Monitor added incrementally)
//
// Runs on the controller node with Docker socket access.
// Tools provisioned inside the Jenkins container: docker CLI, compose plugin,
// python3, node20, pnpm, SonarScanner, trivy.

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

                    echo "===> Test results saved to test-results.xml"
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
            parallel {
                stage('Trivy: backend slim') {
                    steps {
                        sh '''
                            echo "===> Trivy scanning ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG}"

                            mkdir -p security-reports

                            # Human-readable report (table format)
                            trivy image \
                                --severity HIGH,CRITICAL \
                                --ignorefile .trivyignore \
                                --no-progress \
                                --format table \
                                --output security-reports/trivy-backend-slim.txt \
                                ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG} || true

                            # Machine-readable JSON for archiving
                            trivy image \
                                --severity HIGH,CRITICAL \
                                --ignorefile .trivyignore \
                                --no-progress \
                                --format json \
                                --output security-reports/trivy-backend-slim.json \
                                ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG} || true

                            # Show the table in the Jenkins log
                            echo "===> Trivy results (HIGH+CRITICAL) for backend slim:"
                            cat security-reports/trivy-backend-slim.txt

                            # Fail the build if any HIGH/CRITICAL CVEs found (exit code 1)
                            trivy image \
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
                                --severity HIGH,CRITICAL \
                                --ignorefile .trivyignore \
                                --no-progress \
                                --format table \
                                --output security-reports/trivy-frontend.txt \
                                ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG} || true

                            trivy image \
                                --severity HIGH,CRITICAL \
                                --ignorefile .trivyignore \
                                --no-progress \
                                --format json \
                                --output security-reports/trivy-frontend.json \
                                ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG} || true

                            echo "===> Trivy results (HIGH+CRITICAL) for frontend:"
                            cat security-reports/trivy-frontend.txt

                            trivy image \
                                --severity HIGH,CRITICAL \
                                --ignorefile .trivyignore \
                                --no-progress \
                                --exit-code 1 \
                                ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG}
                        '''
                    }
                }
                stage('npm audit (frontend)') {
                    steps {
                        sh '''
                            echo "===> Running pnpm audit on frontend dependencies"
                            mkdir -p security-reports
                            cd frontend

                            # pnpm audit. --audit-level=high means it returns non-zero
                            # for high/critical findings. JSON saved for archival.
                            pnpm audit --audit-level=high --json \
                                > ../security-reports/pnpm-audit.json || \
                                AUDIT_FAILED=true

                            # Human-readable version
                            pnpm audit --audit-level=high \
                                | tee ../security-reports/pnpm-audit.txt || true

                            cd ..
                            echo "===> pnpm audit output:"
                            cat security-reports/pnpm-audit.txt

                            # Re-run to set the actual exit code (pipe above swallowed it)
                            cd frontend
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
