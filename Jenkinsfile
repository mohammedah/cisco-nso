pipeline {
    agent any
    stages {
        stage('Build Master') {
            when {
                branch 'master'
            }
            steps {
                echo 'Building master'
            }
        }
        stage('Build Dev') {
            when {
                branch 'dev'
            }
            steps {
                echo 'Building dev'
            }
        }
        stage('Build uat') {
            when {
                branch 'uat'
            }
            steps {
                echo 'Building dev'
            }
        }
    }
}
