module.exports = function(grunt) {

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        cacheBust: {
            prod: {
                options: {
                    assets: ['**/*.js', '**/*.css'],
                    createCopies: false,
                    baseDir: './prod/blagodarie/'
                },
                files: [{
                    expand: true,
                    cwd: 'prod/blagodarie/',
                    src: ['**/index.html']
                }],
                jsonOutput: false
            },
            dev: {
                options: {
                    assets: ['**/*.js', '**/*.css'],
                    createCopies: false,
                    baseDir: './dev/blagodarie/'
                },
                files: [{
                    expand: true,
                    cwd: 'dev/blagodarie/',
                    src: ['**/index.html']
                }],
                jsonOutput: false
            }
        }


    });

   grunt.loadNpmTasks('grunt-cache-bust'); 
   grunt.registerTask('default', ['cacheBust']);
};
