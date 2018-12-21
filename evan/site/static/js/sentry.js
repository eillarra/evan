Sentry.init({
    dsn: 'https://5b2d2f25df16403cb489cab3213ec892@sentry.io/1426084',
    release: GIT_REV,
    environment: 'production',
    integrations: [new Sentry.Integrations.Vue()],
});

if (USER_ID > 0) {
    Sentry.configureScope(function (scope) {
        scope.setUser({
            id: USER_ID
        });
    });
}
