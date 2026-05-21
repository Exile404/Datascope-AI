// DataScope AI — Jenkins Pipeline
// Stages: Build, Test, Code Quality (Security/Deploy/Release/Monitor added incrementally)
//
// Runs on the controller node with Docker socket access.
// Tools provisioned inside the Jenkins container: docker CLI, compose plugin,
// python3, node20, pnpm, plus the auto-installed SonarScanner.
//
// Triggered by: GitHub push to feature/jenkins-pipeline (later: webhook).

pipeline {
    agent any

    options {
        timestamps()                          // prefix every log line with a timestamp
        timeout(time: 30, unit: 'MINUTES')    // kill the build if it hangs
        buildDiscarder(logRotator(numToKeepStr: '15'))  // keep only the last 15 builds
        disableConcurrentBuilds()             // no two builds at once (avoids port + volume clashes)
    }

    environment {
        // Image tags carry the build number so each pipeline run is traceable
        BACKEND_SLIM_TAG = "slim-${env.BUILD_NUMBER}"
        BACKEND_FULL_TAG = "full-${env.BUILD_NUMBER}"
        FRONTEND_TAG     = "fe-${env.BUILD_NUMBER}"
        MOCK_TAG         = "mock-${env.BUILD_NUMBER}"

        // Cosmetic prefix that shows up in the Blue Ocean view
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
                            echo "===> Image size:"
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
                    // Resolve the SonarScanner tool that Jenkins auto-downloads
                    def scannerHome = tool 'SonarScanner'

                    withCredentials([string(credentialsId: 'sonarcloud-token', variable: 'SONAR_TOKEN')]) {
                        sh """
                            echo '===> Running SonarCloud analysis'
                            ${scannerHome}/bin/sonar-scanner \\
                                -Dsonar.host.url=https://sonarcloud.io \\
                                -Dsonar.token=\$SONAR_TOKEN \\
                                -Dsonar.projectKey=Exile404_Datascope-AI \\
                                -Dsonar.organization=exile404 \\
                                -Dsonar.branch.name=${env.BRANCH_NAME ?: 'feature/jenkins-pipeline'}
                        """
                    }
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
            // Clean up images created during this build (saves disk on the host)
            sh '''
                docker rmi ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG} || true
                docker rmi ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG} || true
                docker rmi ${REGISTRY_PREFIX}-ollama-mock:${MOCK_TAG} || true
            '''
        }
    }
}
