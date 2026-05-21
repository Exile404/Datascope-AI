// DataScope AI — Jenkins Pipeline
// Stages: Build, Test (more added incrementally)
//
// Runs on the controller node with Docker socket access.
// Tools provisioned inside the Jenkins container: docker CLI, compose plugin, python3, node20, pnpm.
//
// Triggered by: GitHub push to feature/jenkins-pipeline (later: webhook).

pipeline {
    agent any

    options {
        timestamps()                          // prefix every log line with a timestamp
        timeout(time: 30, unit: 'MINUTES')    // kill the build if it hangs
        buildDiscarder(logRotator(numToKeepStr: '15'))  // keep only the last 15 builds
        disableConcurrentBuilds()             // no two builds at once (avoids port + volume clashes)
        ansiColor('xterm')                    // colourise log output where supported
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
                // Jenkins already cloned via the job's SCM config; this just logs what we got.
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
                    // Publish results to Jenkins UI even on failure, so we can see what broke
                    junit testResults: 'backend/test-results.xml', allowEmptyResults: false
                    archiveArtifacts artifacts: 'backend/coverage.xml', allowEmptyArchive: true
                }
            }
        }
    }

    post {
        success {
            echo "===> ✅ Pipeline succeeded for build #${env.BUILD_NUMBER}"
        }
        failure {
            echo "===> ❌ Pipeline failed for build #${env.BUILD_NUMBER}"
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
