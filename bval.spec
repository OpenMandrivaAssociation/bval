%{?_javapackages_macros:%_javapackages_macros}
%global namedreltag %{nil}
%global namedversion %{version}%{?namedreltag}
# disable guice module for now
%global with_guice 0
Name:          bval
Version:       0.5
Release:       7.0%{?dist}
Summary:       Apache Bean Validation
License:       ASL 2.0
Url:           http://bval.apache.org/
Source0:       http://www.apache.org/dist/%{name}/%{namedversion}/%{name}-parent-%{namedversion}-source-release.zip
# add JSR303 full support
Source1:       %{name}-0.5-depmap
Patch0:        %{name}-0.3-incubating-core-FeaturesCapable.patch
# fix jaxb 2.2 apis
Patch1:        %{name}-0.4-jsr303-fix-jaxb-apis.patch

BuildRequires: java-devel >= 0:1.7.0

BuildRequires: apache-commons-beanutils
BuildRequires: apache-commons-lang3
#BuildRequires: bean-validation-api provides incopatible JSR349 APIs
BuildRequires: freemarker
BuildRequires: geronimo-parent-poms
BuildRequires: geronimo-validation
BuildRequires: glassfish-jaxb
BuildRequires: glassfish-jaxb-api
BuildRequires: hibernate-jpa-2.0-api
BuildRequires: slf4j
BuildRequires: xstream

%if %with_guice
BuildRequires: aopalliance
BuildRequires: atinject
BuildRequires: google-guice
%endif

# test deps
BuildRequires: geronimo-osgi-support
BuildRequires: junit
BuildRequires: mockito

BuildRequires: apache-rat-plugin
BuildRequires: buildnumber-maven-plugin
BuildRequires: maven-antrun-plugin
BuildRequires: maven-enforcer-plugin
BuildRequires: jaxb2-maven-plugin
BuildRequires: maven-local
BuildRequires: maven-plugin-bundle
BuildRequires: maven-surefire-provider-junit4
# force JSR303 apis
Requires:      geronimo-validation
BuildArch:     noarch

%description
Apache BVal delivers an implementation of the Bean Validation
Specification (JSR303), which is TCK compliant and
works on Java SE 5 or later. The initial codebase for the
project was donated to the ASF by a SGA from Agimatec GmbH.

%package javadoc
Summary:       Javadoc for %{name}

%description javadoc
This package contains javadoc for %{name}.

%prep
%setup -q -n %{name}-parent-%{namedversion}
find . -name "*.class" -delete
find . -name "*.jar" -delete

%patch0 -p0
%patch1 -p0

# Don't use buildnumber-plugin, because jna is required and currently broken in f17
%pom_remove_plugin org.codehaus.mojo:buildnumber-maven-plugin

%pom_remove_plugin org.codehaus.mojo:findbugs-maven-plugin
%pom_remove_plugin org.codehaus.mojo:findbugs-maven-plugin bval-xstream
%pom_remove_plugin org.codehaus.mojo:ianal-maven-plugin
%pom_remove_plugin org.codehaus.mojo:jdepend-maven-plugin


%pom_remove_dep org.apache.geronimo.specs:geronimo-jpa_2.0_spec
%pom_xpath_inject "pom:project/pom:dependencyManagement/pom:dependencies" "
  <dependency>
    <groupId>org.hibernate.javax.persistence</groupId>
    <artifactId>hibernate-jpa-2.0-api</artifactId>
    <version>1.0.1.Final</version>
  </dependency>"

%if %with_guice
# require guice with aop support
# build failure bval-guice/src/main/java/org/apache/bval/guice/ValidationModule.java:[61,12] error: cannot find symbol
%pom_remove_dep org.apache.bval:org.apache.bval.bundle bval-guice
%pom_xpath_inject "pom:project/pom:dependencies" '
  <dependency>
    <groupId>org.apache.bval</groupId>
    <artifactId>bval-core</artifactId>
    <version>${project.version}</version>
  </dependency>
  <dependency>
    <groupId>org.apache.bval</groupId>
    <artifactId>bval-jsrjsrjsr303</artifactId>
    <version>${project.version}</version>
  </dependency>' bval-guice
%else
%pom_disable_module bval-guice
%endif
%pom_remove_dep org.apache.bval:org.apache.bval.bundle bval-extras
%pom_xpath_inject "pom:project/pom:dependencies" '
  <dependency>
    <groupId>org.apache.bval</groupId>
    <artifactId>bval-core</artifactId>
    <version>${project.version}</version>
  </dependency>' bval-extras
%if 0%{?fedora}
%pom_xpath_inject "pom:project/pom:dependencies" '
  <dependency>
    <groupId>org.apache.bval</groupId>
    <artifactId>bval-jsr303</artifactId>
    <version>${project.version}</version>
  </dependency>' bval-extras
%else
%pom_disable_module bval-jsr303
%endif

# fix koji build problems missing org.apache.geronimo.osgi.locator.ProviderLocator
%pom_xpath_inject "pom:project/pom:dependencies" '
  <dependency>
    <groupId>org.apache.geronimo.specs</groupId>
    <artifactId>geronimo-osgi-locator</artifactId>
    <version>1.0</version>
    <scope>test</scope>
  </dependency>' bval-jsr303

%pom_remove_dep :geronimo-jpa_2.0_spec bval-jsr303
%pom_xpath_inject "pom:project/pom:dependencies" '
  <dependency>
    <groupId>org.hibernate.javax.persistence</groupId>
    <artifactId>hibernate-jpa-2.0-api</artifactId>
    <scope>provided</scope>
    <optional>true</optional>
  </dependency>' bval-jsr303
  
# unavailable deps
# org.hibernate.jsr303.tck jsr303-tck 1.0.6.GA
# org.jboss.test-harness jboss-test-harness-jboss-as-51 1.0.0
%pom_disable_module bval-tck

%pom_disable_module bundle

# fix non ASCII chars
for s in bval-extras/src/main/java/org/apache/bval/extras/constraints/net/DomainValidator.java;do
  native2ascii -encoding UTF8 ${s} ${s}
done

%build

%mvn_file :%{name}-core %{name}/core
%mvn_file :%{name}-extras %{name}/extras
%mvn_file :%{name}-json %{name}/json
%if 0%{?fedora}
%mvn_file :%{name}-jsr303 %{name}/jsr303
%endif
%mvn_file :%{name}-xstream %{name}/xstream

%mvn_build -- -Dri -Dproject.build.sourceEncoding=UTF-8 \
 -Dmaven.local.depmap.file="%{SOURCE1}"

%install
%mvn_install 

%files -f .mfiles
%dir %{_javadir}/%{name}
%doc CHANGES.txt LICENSE NOTICE README.txt

%files javadoc -f .mfiles-javadoc
%doc LICENSE NOTICE

%changelog
* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.5-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Fri Jul 05 2013 gil cattaneo <puntogil@libero.it> 0.5-6
- fix unowned directory

* Fri Jul 05 2013 gil cattaneo <puntogil@libero.it> 0.5-5
- switch to XMvn
- minor changes to adapt to current guideline

* Sun Feb 17 2013 gil cattaneo <puntogil@libero.it> 0.5-4
- added missing BR geronimo-parent-poms

* Sun Feb 17 2013 gil cattaneo <puntogil@libero.it> 0.5-3
- added missing BR maven-local

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Mon Sep 24 2012 gil cattaneo <puntogil@libero.it> 0.5-1
- update to 0.5
- used pom macros

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Jul 12 2012 gil cattaneo <puntogil@libero.it> 0.4-2
- Installed NOTICE file in javadoc package
- Fix preserve timestamps of installed POM files

* Tue May 15 2012 gil cattaneo <puntogil@libero.it> 0.4-1
- update to 0.4

* Fri Apr 06 2012 gil cattaneo <puntogil@libero.it> 0.3-1
- initial rpm