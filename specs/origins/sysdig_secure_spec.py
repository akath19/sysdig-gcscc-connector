from mamba import description, it, before, context
from expects import expect, have_key, end_with, start_with, have_len, equal, be_below_or_equal
from doublex import Stub, when

import securecscc
from securecscc import origins

from specs.support import fixtures
from specs.support.matchers import be_the_organization_resource_name


with description(origins.SysdigSecure) as self:
    with before.each:
        self.settings = securecscc.Settings()
        self.sysdig_client = Stub(securecscc.SysdigSecureClient)
        self.gcloud_client = Stub(securecscc.GoogleCloudClient)
        self.mapper = origins.SysdigSecure(self.settings,
                                           self.sysdig_client,
                                           self.gcloud_client)

        self.organization = self.settings.organization()

    with context('when checking the finding_id'):
        with it('uses id from security event'):
            finding = self.mapper.create_from(fixtures.event())

            expect(finding.finding_id).to(equal('721918015150567424'))

        with it('uses a shorter value than allowed by Google'):
            finding = self.mapper.create_from(fixtures.event())

            expect(finding.finding_id).to(have_len(be_below_or_equal(32)))

    with it('uses Sysdig Secure as source'):
        finding = self.mapper.create_from(fixtures.event())

        expect(finding.source).to(equal(self.settings.source()))

    with it('uses only seconds from event time'):
        finding = self.mapper.create_from(fixtures.event())

        expect(finding.event_time).to(equal(1568647020))

    with it('retrieves category name from sysdig client'):
        category_name = 'Write below root'

        finding = self.mapper.create_from(fixtures.event())

        expect(finding.category).to(equal(category_name))

    with context('when building the URL'):
        with it('allows setting an url for on premise instances'):
            finding = self.mapper.create_from(fixtures.event())

            expect(finding.url).to(start_with(self.settings.sysdig_url_prefix()))

        with it('extracts url path from security event'):
            finding = self.mapper.create_from(fixtures.event())

            expect(finding.url).to(end_with('/#/events/f:1568646960,t:1568647080/*/*?viewAs=list'))

    with it('adds output'):
        output = "File below / or /root opened for writing (user=root command=touch /foobarbaz parent=bash file=/foobarbaz program=touch container_id=c8c4d64fe7a5 image=nginx)"

        finding = self.mapper.create_from(fixtures.event())

        expect(finding.summary).to(equal(output))

    with it('adds severity'):
        finding = self.mapper.create_from(fixtures.event())

        expect(finding.severity).to(equal(4))

    with it('adds rule type'):
        finding = self.mapper.create_from(fixtures.event())

        expect(finding.rule_type).to(equal('RULE_TYPE_FALCO'))

    with it('retrieves container metadata'):
        container_id = 'c8c4d64fe7a5'
        when(self.sysdig_client).find_container_metadata_from_container_id(container_id).returns({'container.stuff': 'FOO'})

        finding = self.mapper.create_from(fixtures.event())

        expect(finding.container_metadata).to(have_key('container.stuff', 'FOO'))

    with context('when choosing the resource name'):
        with before.each:
            self.mac = "42:01:0a:9c:0f:ce"
            self.hostname = 'any hostname'

        with it('queries google for its resource_name and adds to asset ids'):
            a_resource_name = 'irrelevant resource name'
            when(self.sysdig_client).find_host_by_mac(self.mac).returns(self.hostname)
            when(self.gcloud_client).get_resource_name_from_hostname(self.settings.organization(), self.hostname).returns(a_resource_name)

            finding = self.mapper.create_from(fixtures.event())

            expect(finding.resource_name).to(equal(a_resource_name))

        with context('and mac is not found on sysdig'):
            with it('returns organization as asset id'):
                when(self.sysdig_client).find_host_by_mac(self.mac).returns(None)

                finding = self.mapper.create_from(fixtures.event())

                expect(finding.resource_name).to(be_the_organization_resource_name())

        with context('and hostname is not found on google compute'):
            with it('returns organization as asset id'):
                when(self.sysdig_client).find_host_by_mac(self.mac).returns(self.hostname)
                when(self.gcloud_client).get_resource_name_from_hostname(
                    self.settings.organization(),
                    self.hostname
                ).returns(None)

                finding = self.mapper.create_from(fixtures.event())

                expect(finding.resource_name).to(be_the_organization_resource_name())

    with context('when receving a host event'):
        with before.each:
            self.mac = "42:01:0a:9c:00:06"

        with it('includes instance id in asset ids'):
            hostname = "irrelevant hostname"
            a_resource_name = "irrelevant resource_name"
            when(self.sysdig_client).find_host_by_mac(self.mac).returns(hostname)
            when(self.gcloud_client).get_resource_name_from_hostname(
                self.settings.organization(), hostname
            ).returns(a_resource_name)

            finding = self.mapper.create_from(fixtures.event_host())

            expect(finding.resource_name).to(equal(a_resource_name))

        with it('does not add any container metadata'):
            finding = self.mapper.create_from(fixtures.event_host())

            expect(finding.container_metadata).to(equal({}))
