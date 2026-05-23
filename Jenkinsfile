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
    parameters {
        string(
            name: 'RELEASE_TAG',
            defaultValue: '',
            description: 'Set to a version like "v1.0.0" to manually trigger a production release. Leave empty for normal CI runs. (Auto-set via TAG_NAME if pipeline is triggered by a git tag push.)'
        )
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
                            HEALTH=$(curl -sf http://host.docker.internal:8001/health)
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
                            RESPONSE=$(curl -sf -X POST http://host.docker.internal:8001/api/cost/calculate \\
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
                            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://host.docker.internal:3001/)
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
                stage('Tag :staging') {
                    steps {
                        sh '''
                            echo "===> Tagging validated images as :staging"

                            docker tag ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG} \\
                                       ${REGISTRY_PREFIX}-backend:staging
                            docker tag ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG} \\
                                       ${REGISTRY_PREFIX}-frontend:staging
                            docker tag ${REGISTRY_PREFIX}-ollama-mock:${MOCK_TAG} \\
                                       ${REGISTRY_PREFIX}-ollama-mock:staging

                            echo ""
                            echo "===> :staging tags now point to:"
                            docker images --format "{{.Repository}}:{{.Tag}} -> {{.ID}}" \\
                                | grep -E ":(staging|${BACKEND_SLIM_TAG}|${FRONTEND_TAG}|${MOCK_TAG})\\$" \\
                                | sort
                        '''
                    }
                }
                stage('Rollback Verification') {
                    steps {
                        sh '''
                            echo "===> Rollback drill: simulate a backend failure"
                            echo "===> after a successful deploy and verify our health"
                            echo "===> probe correctly detects the degraded state."
                            echo ""

                            echo "===> Step 1: confirm backend is currently healthy"
                            INITIAL=$(curl -sf http://host.docker.internal:8001/health || echo "FAILED_AT_START")
                            echo "Pre-kill probe: $INITIAL"
                            if [ "$INITIAL" = "FAILED_AT_START" ]; then
                                echo "ERROR: backend was not healthy before the drill even started."
                                echo "Something is wrong with the stack. Aborting."
                                exit 1
                            fi
                            echo ""

                            echo "===> Step 2: kill the backend container"
                            docker kill datascope-backend-staging
                            echo "Backend killed."
                            echo ""

                            echo "===> Step 3: wait briefly for Docker to register the death"
                            sleep 5
                            echo "Container state:"
                            docker compose -f docker-compose.staging.yml ps backend
                            echo ""

                            echo "===> Step 4: probe health; we EXPECT this to fail"
                            POST_KILL=$(curl -sf -m 5 http://host.docker.internal:8001/health 2>&1 || echo "PROBE_FAILED_AS_EXPECTED")
                            echo "Post-kill probe: $POST_KILL"
                            echo ""

                            if echo "$POST_KILL" | grep -q "PROBE_FAILED_AS_EXPECTED"; then
                                echo "===> PASS: health probe correctly detected the failure"
                                echo "===> In a real deploy this would trigger rollback to the"
                                echo "===> previously-validated :staging image."
                            else
                                echo "===> FAIL: backend responded despite being killed."
                                echo "===> Our health probe cannot be trusted to gate deployments."
                                exit 1
                            fi
                        '''
                    }
                }
                stage('Final Teardown') {
                    steps {
                        sh '''
                            echo "===> Tearing down staging stack"
                            echo "===> (Image :staging tags persist, so a known-good"
                            echo "===> reference deploy can be re-launched any time.)"
                            echo ""

                            docker compose -f docker-compose.staging.yml down -v --remove-orphans

                            echo ""
                            echo "===> Verifying clean state"
                            REMAINING=$(docker ps -a --filter "name=datascope-.*-staging" --format "{{.Names}}")
                            if [ -n "$REMAINING" ]; then
                                echo "WARNING: leftover staging containers detected:"
                                echo "$REMAINING"
                            else
                                echo "PASS: no leftover staging containers"
                            fi

                            echo ""
                            echo "===> :staging-tagged images still available:"
                            docker images --filter "reference=*:staging" \\
                                --format "{{.Repository}}:{{.Tag}} ({{.Size}})" || true
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
        stage('Release (production)') {
            when {
                anyOf {
                    tag pattern: "v*", comparator: "GLOB"
                    expression {
                        return params.RELEASE_TAG?.trim() ? params.RELEASE_TAG.startsWith('v') : false
                    }
                }
            }
            environment {
                // VERSION_TAG resolves in priority: param > env tag > error.
                // params.RELEASE_TAG is set when triggered manually with the parameter.
                // env.TAG_NAME is set automatically by Jenkins when triggered by a tag push.
                VERSION_TAG = "${params.RELEASE_TAG?.trim() ?: env.TAG_NAME ?: 'unknown'}"
            }
            stages {
                stage('Snapshot Previous Production') {
                    steps {
                        sh '''
                            echo "===> Snapshotting current :production images as :production-rollback"
                            echo "===> (so we can restore them if this release fails smoke tests)"
                            echo ""

                            for svc in backend frontend ollama-mock; do
                                # If a :production tag exists, snapshot it. If not, this is the
                                # first ever release, so skip with a note.
                                if docker image inspect "${REGISTRY_PREFIX}-${svc}:production" >/dev/null 2>&1; then
                                    docker tag "${REGISTRY_PREFIX}-${svc}:production" \\
                                               "${REGISTRY_PREFIX}-${svc}:production-rollback"
                                    echo "Snapshotted: ${REGISTRY_PREFIX}-${svc}:production -> :production-rollback"
                                else
                                    echo "No existing :production tag for ${svc}, skipping snapshot."
                                    echo "(First release ever, no rollback target until next time.)"
                                fi
                            done
                        '''
                    }
                }

                stage('Promote :staging to :production') {
                    steps {
                        sh '''
                            echo "===> Promoting :staging images to :production and :${VERSION_TAG}"
                            echo ""

                            for svc in backend frontend ollama-mock; do
                                # Verify :staging exists first (sanity check; if Deploy stage ran,
                                # :staging should always exist by this point).
                                if ! docker image inspect "${REGISTRY_PREFIX}-${svc}:staging" >/dev/null 2>&1; then
                                    echo "ERROR: ${REGISTRY_PREFIX}-${svc}:staging not found."
                                    echo "Did the Deploy stage tag this image? Aborting release."
                                    exit 1
                                fi

                                docker tag "${REGISTRY_PREFIX}-${svc}:staging" \\
                                           "${REGISTRY_PREFIX}-${svc}:production"
                                docker tag "${REGISTRY_PREFIX}-${svc}:staging" \\
                                           "${REGISTRY_PREFIX}-${svc}:${VERSION_TAG}"
                                echo "Promoted: ${REGISTRY_PREFIX}-${svc}:staging"
                                echo "       -> :production"
                                echo "       -> :${VERSION_TAG}"
                            done

                            echo ""
                            echo "===> Tag summary:"
                            docker images --format "{{.Repository}}:{{.Tag}}" \\
                                | grep -E "(${VERSION_TAG}|production|production-rollback)\\$" \\
                                | sort
                        '''
                    }
                }

                stage('Bring Up Production') {
                    steps {
                        sh '''
                            echo "===> Bringing up production stack via docker-compose.prod.yml"
                            echo ""

                            # Tear down any leftover prod stack (e.g. from a previous failed release).
                            docker compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

                            # Compose reads BACKEND_TAG / FRONTEND_TAG via env vars in the YAML.
                            # We set them to 'production' so prod runs the just-promoted images.
                            export BACKEND_TAG=production
                            export FRONTEND_TAG=production

                            docker compose -f docker-compose.prod.yml up -d

                            echo ""
                            echo "===> Waiting for production services to report healthy (max 90s)"

                            for i in $(seq 1 18); do
                                STATUS=$(docker compose -f docker-compose.prod.yml ps --format "{{.Name}}|{{.Health}}")
                                echo "Attempt $i:"
                                echo "$STATUS"

                                BAD=$(echo "$STATUS" | grep -E "unhealthy|starting|Exited|Restarting" || true)
                                if [ -z "$BAD" ]; then
                                    echo ""
                                    echo "===> Production stack healthy"
                                    break
                                fi

                                if [ $i -eq 18 ]; then
                                    echo ""
                                    echo "===> TIMEOUT: production not healthy after 90s"
                                    docker compose -f docker-compose.prod.yml logs --tail=80
                                    exit 1
                                fi

                                sleep 5
                            done

                            echo ""
                            echo "===> Final production stack status:"
                            docker compose -f docker-compose.prod.yml ps
                        '''
                    }
                }

                stage('Smoke Test Production') {
                    steps {
                        sh '''
                            echo "===> Running 3 smoke tests against production"
                            echo ""

                            echo "===> 1/3 backend /health"
                            HEALTH=$(curl -sf http://host.docker.internal:8000/health)
                            echo "Response: $HEALTH"
                            echo "$HEALTH" | grep -q '"api":"ok"' || { echo "FAIL: /health api not ok"; exit 1; }
                            echo "PASS"
                            echo ""

                            echo "===> 2/3 backend happy path"
                            RESPONSE=$(curl -sf -X POST http://host.docker.internal:8000/api/cost/calculate \\
                                -H "Content-Type: application/json" \\
                                -d '{"model":"gpt-4o","input_tokens":1000000,"output_tokens":500000}')
                            echo "Response: $RESPONSE"
                            echo "$RESPONSE" | grep -q '"total_cost":7.5' || { echo "FAIL: total_cost != 7.5"; exit 1; }
                            echo "PASS"
                            echo ""

                            echo "===> 3/3 frontend homepage"
                            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://host.docker.internal:3000/)
                            echo "HTTP code: $HTTP_CODE"
                            [ "$HTTP_CODE" = "200" ] || { echo "FAIL: frontend not 200"; exit 1; }
                            echo "PASS"
                            echo ""

                            echo "===> Production release ${VERSION_TAG} VALIDATED"
                            echo "===> Production stack remains running."
                            echo "===> :production-rollback tag preserves the previous version."
                        '''
                    }
                }
            }
            post {
                failure {
                    sh '''
                        echo "===> RELEASE FAILED: rolling back to previous :production"
                        echo "===> (i.e. the snapshot taken at start of this release)"
                        echo ""

                        echo "===> Step 1: tear down the failed new prod stack"
                        docker compose -f docker-compose.prod.yml logs --tail=100 || true
                        docker compose -f docker-compose.prod.yml down --remove-orphans || true

                        echo ""
                        echo "===> Step 2: restore :production-rollback to :production"
                        ROLLED_BACK=0
                        for svc in backend frontend ollama-mock; do
                            if docker image inspect "${REGISTRY_PREFIX}-${svc}:production-rollback" >/dev/null 2>&1; then
                                docker tag "${REGISTRY_PREFIX}-${svc}:production-rollback" \\
                                           "${REGISTRY_PREFIX}-${svc}:production"
                                echo "Restored: ${REGISTRY_PREFIX}-${svc}:production-rollback -> :production"
                                ROLLED_BACK=1
                            else
                                echo "No :production-rollback for ${svc}, nothing to restore."
                            fi
                        done

                        if [ "$ROLLED_BACK" = "1" ]; then
                            echo ""
                            echo "===> Step 3: bring up rolled-back production stack"
                            export BACKEND_TAG=production
                            export FRONTEND_TAG=production
                            docker compose -f docker-compose.prod.yml up -d
                            sleep 15
                            echo ""
                            echo "===> Step 4: verify rolled-back stack:"
                            docker compose -f docker-compose.prod.yml ps
                            echo ""
                            echo "===> ROLLBACK COMPLETE. Build marked failed; prod is on previous version."
                        else
                            echo ""
                            echo "===> No rollback target existed (this was the first release ever)."
                            echo "===> Prod is now empty. Build marked failed."
                        fi
                    '''
                }
            }
        }

        // ----------------------------------------------------------------
        // Monitor: verify the observability stack is healthy AFTER release,
        // and annotate Grafana with the deploy event so dashboards show a
        // marker at the moment this build went live in production.
        //
        // Skipped for non-prod-promotion builds (no point annotating prod
        // dashboards when prod was not touched). Soft-fails: if the monitor
        // stack is offline, the build is marked UNSTABLE rather than
        // FAILURE so a monitoring outage does not roll back a good deploy.
        // ----------------------------------------------------------------
        stage('Monitor (post-release verification)') {
            when {
                anyOf {
                    tag pattern: "v*", comparator: "GLOB"
                    expression {
                        return params.RELEASE_TAG?.trim() ? params.RELEASE_TAG.startsWith('v') : false
                    }
                }
            }
            steps {
                script {
                    def monitorOk = true

                    // 1. Health endpoints
                    def checks = [
                        [name: 'Prometheus health',   url: 'http://host.docker.internal:9091/-/healthy'],
                        [name: 'Grafana health',      url: 'http://host.docker.internal:3002/api/health'],
                        [name: 'Alertmanager health', url: 'http://host.docker.internal:9093/-/healthy'],
                    ]
                    for (c in checks) {
                        def rc = sh(returnStatus: true,
                                    script: "curl -fsS --max-time 5 -o /dev/null '" + c.url + "'")
                        if (rc != 0) {
                            echo "===> [WARN] ${c.name} unreachable at ${c.url}"
                            monitorOk = false
                        } else {
                            echo "===> [OK]   ${c.name}"
                        }
                    }

                    // 2. Prometheus scrape targets all 'up'
                    def targetsRc = sh(returnStatus: true, script: """
                        set -eu
                        curl -fsS --max-time 5 http://host.docker.internal:9091/api/v1/targets > /tmp/targets.json
                        python3 -c '
import json, sys
d = json.load(open("/tmp/targets.json"))
bad = [t for t in d["data"]["activeTargets"] if t["health"] != "up"]
if bad:
    for t in bad:
        print("DOWN:", t["labels"].get("job","?"), "->", t.get("scrapeUrl","?"))
    sys.exit(2)
print("all targets up")
'
                    """)
                    if (targetsRc != 0) {
                        echo "===> [WARN] one or more Prometheus targets are down"
                        monitorOk = false
                    } else {
                        echo "===> [OK]   all Prometheus targets up"
                    }

                    // 3. Annotate Grafana with deploy event
                    withCredentials([string(credentialsId: 'grafana-deploy-token', variable: 'GRAFANA_TOKEN')]) {
                        def buildNum = env.BUILD_NUMBER
                        def releaseTag = params.RELEASE_TAG?.trim() ?: env.TAG_NAME ?: 'unknown'
                        def payload = '{"text":"Deploy: build #' + buildNum +
                                      ' promoted to production (tag ' + releaseTag +
                                      ')","tags":["deploy","production","jenkins","build-' + buildNum + '"]}'
                        def arc = sh(returnStatus: true, script:
                            "curl -fsS --max-time 5 -X POST " +
                            "http://host.docker.internal:3002/api/annotations " +
                            "-H 'Authorization: Bearer ${GRAFANA_TOKEN}' " +
                            "-H 'Content-Type: application/json' " +
                            "-d '" + payload + "'"
                        )
                        if (arc != 0) {
                            echo "===> [WARN] failed to write Grafana annotation"
                            monitorOk = false
                        } else {
                            echo "===> [OK]   Grafana annotation written for build #${buildNum}"
                        }
                    }

                    if (!monitorOk) {
                        currentBuild.result = 'UNSTABLE'
                        echo "===> Monitor stage flagged issues; build marked UNSTABLE (deploy itself was successful)."
                    } else {
                        echo "===> Monitor stage: all checks green."
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
            sh '''
                docker rmi ${REGISTRY_PREFIX}-backend:${BACKEND_SLIM_TAG} || true
                docker rmi ${REGISTRY_PREFIX}-frontend:${FRONTEND_TAG} || true
                docker rmi ${REGISTRY_PREFIX}-ollama-mock:${MOCK_TAG} || true
            '''
        }
    }
}
