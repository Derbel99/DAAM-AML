public with sharing class AmlScreeningService {
    public class AmlException extends Exception {}

    // true = correspondance dans la liste fictive; une erreur leve une exception.
    public static Boolean screen(String firstName, String lastName, Date dateOfBirth) {
        if (String.isBlank(firstName) || String.isBlank(lastName) || dateOfBirth == null) {
            throw new AmlException('Prenom, nom et date de naissance requis.');
        }
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:AML_Mock/v1/aml/screen');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setTimeout(10000);
        req.setBody(JSON.serialize(new Map<String, Object>{
            'firstName' => firstName, 'lastName' => lastName, 'dateOfBirth' => dateOfBirth
        }));
        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() != 200) {
            throw new AmlException('Echec verification AML. HTTP ' + res.getStatusCode());
        }
        try {
            Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            if (body == null || !(body.get('isFlagged') instanceof Boolean)) {
                throw new AmlException('Reponse AML invalide.');
            }
            return (Boolean) body.get('isFlagged');
        } catch (Exception e) {
            throw new AmlException('Reponse AML invalide.');
        }
    }
}
