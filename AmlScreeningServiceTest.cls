@IsTest
private class AmlScreeningServiceTest {
    private class MockResponse implements HttpCalloutMock {
        private Integer status;
        private String body;
        MockResponse(Integer status, String body) { this.status = status; this.body = body; }
        public HttpResponse respond(HttpRequest req) {
            System.assertEquals('callout:AML_Mock/v1/aml/screen', req.getEndpoint());
            System.assertEquals('POST', req.getMethod());
            Map<String, Object> sent = (Map<String, Object>) JSON.deserializeUntyped(req.getBody());
            System.assertEquals('1980-01-15', sent.get('dateOfBirth'));
            HttpResponse res = new HttpResponse();
            res.setStatusCode(status);
            res.setBody(body);
            return res;
        }
    }
    @IsTest static void flagged() {
        Test.setMock(HttpCalloutMock.class, new MockResponse(200, '{"isFlagged":true}'));
        System.assertEquals(true, AmlScreeningService.screen('Alex', 'TestAlerte', Date.newInstance(1980, 1, 15)));
    }
    @IsTest static void clearResult() {
        Test.setMock(HttpCalloutMock.class, new MockResponse(200, '{"isFlagged":false}'));
        System.assertEquals(false, AmlScreeningService.screen('Alex', 'TestClair', Date.newInstance(1980, 1, 15)));
    }
    @IsTest static void failuresAreNotClearResults() {
        for (String body : new List<String>{'{}', 'null', 'invalid', '{"isFlagged":"false"}'}) {
            Test.setMock(HttpCalloutMock.class, new MockResponse(200, body));
            Boolean failed = false;
            try { AmlScreeningService.screen('Alex', 'TestAlerte', Date.newInstance(1980, 1, 15)); }
            catch (AmlScreeningService.AmlException e) { failed = true; }
            System.assert(failed);
        }
        Test.setMock(HttpCalloutMock.class, new MockResponse(503, '{}'));
        Boolean failed = false;
        try { AmlScreeningService.screen('Alex', 'TestAlerte', Date.newInstance(1980, 1, 15)); }
        catch (AmlScreeningService.AmlException e) { failed = true; }
        System.assert(failed);
    }
}
